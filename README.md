# mod-notification-handler
handles communicating with moderators related to moderatering submissions

running:
currently there isnt a setup for this to be run locally because it requires a pubsub queue to pull data from

testing:
tests are set up to run on most individual functions and use test data in data.sql

```
poetry install
poetry run coverage run -m pytest
```
