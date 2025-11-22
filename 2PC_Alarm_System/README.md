# Distributed-Alarm-System

There are two different distributed system architectures used to develop similar apps.
Microservice based architecture using gRPC to communicate between nodes
and a Resource Based architecture using HTTP to communicate between nodes.

## Frontend Application Overview
The core required key functionalities provided in both apps are as follows:
1) Add alarms 
2) Update existing alarms
3) Delete alarms
4) List upcoming alarms
5) Notify user based on alarms data

Once the respective applications are up and running, users only need to interact with the provided frontend apps through http://localhost:8080 (microservices) or http://localhost:8081 (resource-based).

Both applications allow users to sign up or sign in. 
- **Disclaimer:** there is no password recovery option, so be sure to remember your credentials. Or you can make another account that does not have the same username.

Once signed in, the dashboard consists of:
* Section to add new alarms:
    * Adding a new alarm is as simple as filling out the corresponding fields for a title/message and time, then clicking the add button.
    * Adding alarms that are before the current time (e.g. adding an alarm for 5:00AM when it is 12:00PM) will be scheduled for the next day.
    * Adding alarms that are at the current time (e.g. adding an alarm for 12:00PM when it is 12:00PM) will be scheduled for the next day.
* Section listing scheduled alarms:
    * This section lists all alarms scheduled and not notified to the user yet. Users are able to edit alarms and change the title/message and/or the trigger time. Users are also able to remove scheduled alarms before the respective trigger times.
* Section listing notifications:
    * This section is how the application notifies its users when an alarm is triggered. When an alarm is due, it is removed from the table (in the Scheduled Alarms section) and a corresponding notification appears in this section. Users are able to dismiss received notifications.

## Locust Testing Overview
This README also contains instructions to run the corresponding applications with Locust. Note that only one of the architectures can be running Locust at a time. In addition, if you are running an architecture without Locust, you cannot run the same architecture with Locust (e.g. it is not possible to run Resource Based Architecture with the Example Fontend App and Resource Based Architecture with Locust). You are able to stop containers and run other containers without needing to use `docker compose down`.

When the Locust container is up and running, visit http://localhost:8089 (for both) to get started. Here you are able to set values such as maximum concurrent users and how many additional users per second. The host URL should already be populated if you used the `docker compose` commands. From there hit the START button to observe statistics.

## Microservice Architecture
### How to run Microservice Architecture
```
cd microservice_based/
docker compose up --build
```
Once the api_gateway_MS container is running, then visit http://localhost:8080.

### How to run the Microservice Architecture with Locust
```
cd microservice_based/locust_MS/
docker compose up --build
```
Once the locust_app_MS container is running visit http://localhost:8089.
* **Disclaimer:** You can only run Locust with one of the architectures at a time, and you cannot run this with the normal Microservice Architecture. Running both at the same time is not possible, so be sure to stop the corresponding container if you wish to run this one.


### Clean Up after running Microservice Based Architecture
```
docker compose down
```
This command works for both the general Microservices and the Locust testing
* For the general Microservice docker compose, be sure to be in the `microservice_based/` directory
* For the Locust testing, be sure to be in the `microservice_based/locust_MS/` directory

## Resource Based Architecture
### How to Run Resource Based Architecture
```
cd resource_based/
docker compose up --build
```
Once the example_frontend_app_RBA container is running, then visit http://localhost:8081.

### How to Run Resource Based Architecture with Locust
```
cd resource_based/locust_RBA/
docker compose up --build
```
Once the locust_app_RBA container is running, then visit http://localhost:8089.
* **Disclaimer:** You can only run Locust with one of the architectures at a time, and you cannot run this with the normal Resource Based Architecture. Running both at the same time is not possible, so be sure to stop the corresponding container if you wish to run this one.

### Clean Up after running Resource Based Architecture
```
docker compose down
```
This command works for both the general Resource Based and the Locust testing
* For the general Resource Based docker compose, be sure to be in the `resource_based/` directory
* For the Locust testing, be sure to be in the `resource_based/locust_RBA/` directory
