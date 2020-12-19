FROM python:3.8
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN apt-get update && \
	apt-get install --assume-yes gettext && \
	pip install correction_helper
RUN pip install -r requirements.txt && \
	./manage.py migrate && \
	./manage.py loaddata initial
	
	

