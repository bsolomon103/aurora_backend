# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable for Django
ENV DJANGO_SETTINGS_MODULE=aurora.settings


# Run the command to start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
