import unittest

from pydantic import ValidationError

from app.schemas.personalization import UserFilterCreate


class UserFilterSchemaTests(unittest.TestCase):
    def test_accepts_complete_user_condition(self) -> None:
        user_filter = UserFilterCreate(
            name="전기 설비",
            job_categories=["전기"],
            experience_min=1,
            experience_max=5,
            minimum_employee_count=10,
        )

        self.assertEqual(user_filter.experience_max, 5)

    def test_rejects_inverted_experience_range(self) -> None:
        with self.assertRaises(ValidationError):
            UserFilterCreate(name="잘못된 경력", experience_min=5, experience_max=1)

    def test_rejects_invalid_minimum_employee_count(self) -> None:
        with self.assertRaises(ValidationError):
            UserFilterCreate(name="잘못된 인원", minimum_employee_count=0)


if __name__ == "__main__":
    unittest.main()
