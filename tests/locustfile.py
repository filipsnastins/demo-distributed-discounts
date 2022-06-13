import random

from locust import HttpUser, task


class FetchDiscountUser(HttpUser):
    user_id_counter = 1

    @task
    def fetch_discount_task(self):
        campaign_id = "1"
        random_user_id = str(random.randint(1, 2147483646) + self.user_id_counter)
        self.client.post(
            f"/api/discounts/{campaign_id}",
            headers={"Authorization": random_user_id},
            name="POST /api/discounts/<campaign_id> - create discount code",
        )
        self.user_id_counter += 1
