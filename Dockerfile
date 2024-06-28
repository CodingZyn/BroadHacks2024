# Use an official Python runtime as the base image
FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

# Install python 3.9
RUN apt-get update && apt-get install -y python3.9 python3-pip sudo

# Set the working directory in the container
WORKDIR /app

RUN sudo apt install -y graphviz graphviz-dev

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the current directory files to the container
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Set the command to run the application
CMD ["python3", "app.py"]
