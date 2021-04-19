"""Coosto API."""
import logging
from datetime import date, datetime, timedelta
from typing import Callable, Generator

import httpx
import singer
import pause

from tap_coosto.cleaners import CLEANERS
from dateutil.rrule import DAILY, rrule

BASE_URL: str = 'https://in.coosto.com'
ENDPOINT_LOGIN: str = '/api/1/users/login'
ENDPOINT_PROJECTS: str = '/api/1/users/projects'
ENDPOINT_RATE_LIMIT: str = '/api/1/users/rate_limit_status'
ENDPOINT_SAVED_QUERIES: str = '/api/1/savedqueries/get_all'
ENDPOINT_RESULTS: str = '/api/1/query/results'
ENDPOINT_DATE: str = '/?since=:start_date:&until=:end_date:'

ENDPOINT_INTERVENTION: str = '/api/1/engagementstats/get_intervention_details'
QUERY_RESULT_PER_PAGE: int = 20


class Coosto:
    """"Coosto API."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize object.

        Arguments:
            username {str} -- Coosto API username
            password {str} -- Coosto API password
        """
        self.username = username
        self.password = password
        self.cookies = {}
        self.logger: logging.Logger = singer.get_logger()
        self._login()
        self.client: httpx.Client = httpx.Client(http2=True)
        self.set_rate_limit()
        self.next_request = None

    def intervention_details(
        self,
        **kwargs: dict,
    ) -> Generator[dict, None, None]:
        """List intervention details (work from support).

        Yields:
            Generator[dict] --  Cleaned Intervention Details
        """
        # Validate the start_date value exists
        start_date_input: str = str(kwargs.get('start_date', ''))

        if not start_date_input:
            raise ValueError('The parameter start_date is required.')

        # Get the Cleaner
        cleaner: Callable = CLEANERS.get('intervention_details', {})

        for date_day in self._start_days_till_now(start_date_input):

            end_of_day = int(date_day) + 86400
            # Replace placeholder in reports path
            date: str = ENDPOINT_DATE.replace(
                ':start_date:',
                date_day,
            ).replace(
                ':end_date:',
                str(end_of_day),
            )
            current_day = datetime.fromtimestamp(int(date_day)).strftime('%Y-%m-%d')
            # Build URL
            url: str = (
                f'{BASE_URL}{ENDPOINT_INTERVENTION}'
                f'{date}'
            )

            self.logger.info(
                f'Recieving Coosto Intervention Details from {current_day}'
            )

            if self.next_request:
                logging.info(f'sleeping until {self.next_request}')
                pause.until(self.next_request)

            response: httpx._models.Response = self.client.get(  # noqa: WPS437
                url,
                cookies=self.cookies,
            )
            sleep_between_requests: float = (60 / self.max_requests)
            seconds: timedelta = timedelta(seconds=sleep_between_requests)
            self.next_request = datetime.now() + seconds

            # Raise error on 4xx and 5xxx
            response.raise_for_status()

            # Create dictionary from response
            response_data: dict = response.json()

            # Yield Cleaned results
            yield from (
                cleaner(row)
                for row in response_data.get('data')
            )

    def _login(self) -> None:
        """Authenticate with the API."""
        payload: dict = {
            'username': self.username,
            'password': self.password,
        }

        response: httpx._models.Response = httpx.post(  # noqa: WPS437
            BASE_URL + ENDPOINT_LOGIN,
            data=payload,
        )
        response.raise_for_status()
        response_data: dict = response.json().get('data', {})

        # Save the cookies
        self.cookies = {'sessionid': response_data.get('sessionid')}
        self.logger.info(f'Logged in as {self.username}')

    def _start_days_till_now(self, start_date: str) -> Generator:
        """Yield YYYY/MM/DD for every day until now.

        Arguments:
            start_date {str} -- Start date e.g. 2020-01-01

        Yields:
            Generator -- Every day until now.
        """
        # Parse input date
        year: int = int(start_date.split('-')[0])
        month: int = int(start_date.split('-')[1].lstrip())
        day: int = int(start_date.split('-')[2].lstrip())

        # Setup start period
        period: date = date(year, month, day)

        # Setup itterator
        dates: rrule = rrule(
            freq=DAILY,
            dtstart=period,
            until=datetime.utcnow(),
        )

        # Yield dates in EPOCH format
        yield from (date_day.strftime('%s') for date_day in dates)

    def rate_limit(self) -> dict:
        """Retrieve the rate limit for the account.

        Returns:
            dict -- Rate limit data
        """
        response: httpx._models.Response = httpx.get(
            BASE_URL + ENDPOINT_RATE_LIMIT,
            cookies=self.cookies,
        )
        response.raise_for_status()
        return response.json().get('data')

    def set_rate_limit(self) -> None:
        """Set the rate limit for the object."""
        rate_dict: dict = self.rate_limit()
        if not rate_dict.get('enabled'):
            return
        self.max_requests = rate_dict.get('max_requests')
        self.logger.info(f'Requests per minute limit: {self.max_requests}')