FROM python:3
WORKDIR /usr/src/app
RUN pip install google-api-python-client
RUN pip install psycopg2
COPY . .
CMD ["python3","-u","scraper.py"]
# ENTRYPOINT ["python3"]
