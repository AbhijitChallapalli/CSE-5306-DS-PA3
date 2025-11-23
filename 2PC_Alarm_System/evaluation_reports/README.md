# Evaluation Reports
These are reports generated using Locust and the corresponding compose.yml files as described in base directory's README.md.

Each Locust worker will register and/or login, then every 1-3 seconds will preform one of the following operations:
- create an alarm (40%)
- delete a notification (20%)
- delete an alarm (20%)
- update alarm details (20%)

Additionally, as the Locust worker is running, they will periodically request for alarms and notifications every second.

The following are device details used to run these tests:
- 12th Gen Intel(R) Core(TM) i7-12650H
- 32GB DDR5-4800 RAM
- 2TB SSD

Evaluations for microservices architecture are under the `evaluation_reports/microservices/` directory.

Evaluations for resource-based architecture are under the `evaluation_reports/resource_based/` directory.

Files are named using this scheme:
```
<arch_acrynm>_<max_users>_<ramp>_<duration>
```
- arch_acrymn:
    - ms:  microservice architecture
    - rba: resource based architecture
- max_users: Max number of concurrent users (integer)
- ramp: Number of new users per second until max_users (integer)
- duration: All are 5m, for 5 minutes

These are the different scenarios covered, all are tested over a duration of approximately 5 minutes:
| Scenario | Number of users (peak concurrency) | Ramp up (users started/second) |
| --- | ---- | -- |
|  1  |    1 |  1 |
|  2  |   50 |  1 |
|  3  |  100 |  1 |
|  4  |  200 |  5 |
|  5  |  500 | 25 |
|  6  | 1000 | 75 |
