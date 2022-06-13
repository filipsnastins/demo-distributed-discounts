# Documentation for demo-distributed-discounts

- [Documentation for demo-distributed-discounts](#documentation-for-demo-distributed-discounts)
  - [Use case and problem description](#use-case-and-problem-description)
  - [Architecture](#architecture)
  - [Concurrency tests with locust](#concurrency-tests-with-locust)
  - [Limitations and further improvements](#limitations-and-further-improvements)
  - [API Reference](#api-reference)
    - [Authentication](#authentication)
    - [Fetch discount code as a user](#fetch-discount-code-as-a-user)
    - [Campaign management as a brand/store/marketplace administrator](#campaign-management-as-a-brandstoremarketplace-administrator)
    - [Error handling](#error-handling)

## Use case and problem description

- From user perspective:

  - Allow users to quickly get a discount code from the marketplace.
  - Ensure that the returned code is unique and belongs only to one user.
  - Ensure that we don't issue more discount codes than are available on the marketplace.

- For system perspective
  - Enable microservice to be scalable
    - If a loyalty campaign will be very popular, it will increase user wait time or latency.
    - We should be able to scale quickly without running into concurrency issues.
  - Discount code fetch microservice might be one of the busiest services in the system.
    - It has to be fast so that user doesn't have to wait long for the code to be generated
  - Don't over-optimize performance early in project
    - Keep it simple.
    - Make changes as you go and learn more about the system.

## Architecture

- User requests are authenticated at ingress API Gateway - with JWT, Bearer tokens or alike tokens.

- User management is handled in a separate service.

- Discount fetch microservice is protected in internal network and receives already authorized requests.

- Data store - PostgreSQL.

- Discount fetch microservice supports concurrency and scaling with table row locks.

  - User sends a request to fetch a discount code.

    1. First available (not locked) discount code is selected and the row is locked.
       - Available codes are stored in `available_discount_codes` table.
       - `FOR UPDATE SKIP LOCKED`
    2. Discount code is moved to `fetched_discount_codes` table.
    3. Discount code row selected in `available_discount_codes` is deleted.
    4. Transaction is committed.

  - Concurrent requests will fetch the next available row and not block each other.

## Concurrency tests with locust

- Tested locally on a laptop with Docker Compose

  - 4 gunicorn workers, 30 DB connection pool
  - 20 locust workers

- Summary

  - Without locks and without unique constraints - system fails silently and assigns the same discount code to many users.
  - Without locks but with unique constraints - system fails immediately with integrity violation errors.
  - With locks and with unique constrains - system works as expected,
    issuing one discount code per user and not overdrawing discount code limit.

- Concurrency problems without `FOR UPDATE SKIP LOCKED` and without unique constraint on discount code id.

  ```
  # Discount code move from available to fetched - conflicts
  /app/src/app/discounts/routes.py:43: SAWarning: DELETE statement on table 'available_discount_codes'
  expected to delete 1 row(s); 0 were matched.
  Please set confirm_deleted_rows=False within the mapper configuration to prevent this warning.
    db.session.commit()

  # Two requests with different users  at the same time select the same discount code
  [2022-06-12 18:15:06 +0300] [10] [DEBUG] POST /api/discounts/1/861286624
  id='5EA3306872' campaign_id=1 user_id='861286624' event='discount_code_created' timestamp='2022-06-12T18:15:06.708808'

  [2022-06-12 18:15:06 +0300] [8] [DEBUG] POST /api/discounts/1/21274989
  id='5EA3306872' campaign_id=1 user_id='21274989' event='discount_code_created' timestamp='2022-06-12T18:15:06.715487'
  ```

  ![No locks, no unique constraints - locust](/assets/01_without_lock_without_unique_locust.png)

  - More codes issued than available on the market. System fails silently.

  ![No locks, no unique constraints - sql](/assets/01_without_lock_without_unique_sql.png)

- After making discount code id unique in the table, immediately getting unique constraint errors.

  ```
  STATEMENT:  INSERT INTO fetched_discount_codes (id, campaign_id, user_id, is_used) VALUES ('D86C6F4F09', 1, '849083867', false)
  ERROR:  duplicate key value violates unique constraint "fetched_discount_codes_id_key"
  ```

  - System fails fast, but doesn't support scaling.

  ![No locks, with unique constraint - locust](/assets/02_without_lock_with_unique_locust.png)

- With `FOR UPDATE SKIP LOCKED` and unique constraints system behaves as expected, issuing one
  discount code per user.

  ![With locks, with unique constraint - locust](/assets/03_with_locks_with_unique_locust.png)

  ![With locks, with unique constraint - sql](/assets/03_with_locks_with_unique_sql.png)

## Limitations and further improvements

- Use real background job queue like celery - for discount code generation.

- Use messaging queue to put events that discount code has been issued to the user.

  - Separate worker service can pickup events and send notifications to marketplace businesses.
  - The service can throttle requests, transform messages to expected format.
  - Not all businesses will have the same format of the event channel.

- As the scaling needs grow, optimize database with table partitioning and vertical scaling.

- Use the same database in auto tests as in production - swap SQLite to PostgreSQL with test-container.

- More diverse test data set.

- Fix flaky tests when testing asynchronous jobs.

## API Reference

- Routes
  - `POST /api/discounts/<campaign_id>`
  - `GET /api/discounts/<campaign_id>`
  - `POST /api/discounts/<campaign_id>/manage/generate-codes`

### Authentication

- Routes are protected with `Authorization` header.
- Provide any numeric value in `Authorization` header, e.g. `"Authorization": "123456"`, which represents `user_id`.
- Value in authorization header mimics JWT and is used as `user_id, e.g., `"Authorization": "123456"`equals to `user_id = 123456`

### Fetch discount code as a user

- `POST /api/discounts/<campaign_id>`

  - Generate new discount code for given campaign and currently authenticated user.

  - Successful status code - 201

  - Request schema - empty request body

  - Response schema

    ```JS
    {
      "id": string;
      "campaign_id": integer;
      "user_id": integer;
      "is_used": boolean;
    }
    ```

  - Response example

    ```JS
    {
      "id": "60E44C210F",
      "campaign_id": 1,
      "user_id": 1
      "is_used": false,
    }
    ```

  - Error codes
    - INVALID_ACCESS_TOKEN (HTTP 401)
    - DISCOUNT_CODE_NOT_AVAILABLE (HTTP 404) - given campaign does not exist
      or all available discount codes for the campaign are exhausted.
    - DISCOUNT_CODE_ALREADY_FETCHED (HTTP 409) - user had already redeemed discount code
      for the campaign. Use GET endpoint for retrieve the code.

- `GET /api/discounts/<campaign_id>`

  - Get already generated discount code for given loyalty campaign and currently authenticated user.

  - Successful status code - 200

  - Response schema

    ```JS
    {
      "id": string;
      "campaign_id": integer;
      "user_id": integer;
      "is_used": boolean;
    }
    ```

  - Response example

    ```JS
    {
      "id": "60E44C210F",
      "campaign_id": 1,
      "user_id": 1
      "is_used": false,
    }
    ```

  - Error codes
    - INVALID_ACCESS_TOKEN (HTTP 401)
    - DISCOUNT_CODE_NOT_FOUND (HTTP 404) - if discount code for given
      campaign and user has not been generated yet.

### Campaign management as a brand/store/marketplace administrator

- `POST /api/discounts/<campaign_id>/manage/generate-codes`

  - Creates new discount code generation job for a given campaign.
  - The job will be processed in the background.

  - Successful status code - 202

  - Request schema

    ```JS
    {
        "discount_codes_count": integer;
    }
    ```

  - Request example

    ```JS
    {
        "discount_codes_count": 1000
    }
    ```

  - Response schema

    ```JS
    {
      "job_id": string;
    }
    ```

  - Response example

    ```JS
    {
      "job_id": "268f72c5-6391-4c35-8e2c-b99fed3e047d";
    }
    ```

  - Error codes
    - INVALID_ACCESS_TOKEN (HTTP 401)
    - REQUEST_VALIDATION_FAILED (HTTP 400)
    - CAMPAIGN_NOT_FOUND (HTTP 404)

### Error handling

- Response for HTTP error codes 4XX and 5XX

- Response schema

  ```JS
  {
    "error_code": string;
    "error_message": string (optional);
  }
  ```

- Response example

  ```JS
  {
    "error_code": "DISCOUNT_CODE_NOT_FOUND"
  }
  ```

  ```JS
  {
    "error_code": "REQUEST_VALIDATION_FAILED",
    "error_message": "'discount_codes_count' must be a positive integer"
  }
  ```

- Generic error codes
  - INVALID_ACCESS_TOKEN (HTTP 401)
  - REQUEST_VALIDATION_FAILED (HTTP 400)
