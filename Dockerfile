FROM python:3.6

RUN pip install twstock lxml requests

ENTRYPOINT ["twstock"]
