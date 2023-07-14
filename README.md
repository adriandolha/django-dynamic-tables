# django-dynamic-tables
The goal is to build a simple backend for a table builder app, where the user can build tables dynamically. 

## REST API

| REQUEST TYPE | ENDPOINT | ACTION |
| ------------ | -------- | ------ |
| POST | /api/table | Generate dynamic Django model based on user provided fields types and titles. The field type can be a string, number, or Boolean.  
| PUT | /api/table/:id | This end point allows the user to update the structure of dynamically generated model.
| POST | /api/table/:id/row | Allows the user to add rows to the dynamically generated model while respecting the model schema
| GET | /api/table/:id/rows | Get all the rows in the dynamically generated model
Please note that for the scope of this app, a user can't create more than 10 tables with 10 rows each.
## Install
I won't go into details how to install postgres, app requirements, run db migrations or start the server.
Just be aware that you need the following env variables (using django-environ):
```
DATABASE_HOST=localhost
DATABASE_NAME=ddt
DATABASE_USER=postgres
DATABASE_PORT=5432
DATABASE_PASSWORD=<YOUR_DB_PASSWORD>
SECRET_KEY=<YOUR_SECRET_KEY>
```