FROM python:3.9
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code/

# to install dialog (needed by firejail)
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && \
	apt-get install --assume-yes gettext firejail && \
	apt-get clean && \
	pip install correction_helper
RUN pip install -r requirements.txt && \
	./manage.py migrate && \
	./manage.py loaddata initial
	
	

