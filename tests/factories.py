import factory

from apps.authentication.models import FreelancerProfile, User, UserRole


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}@example.com")
    email = factory.LazyAttribute(lambda o: o.username)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = UserRole.FREELANCER

class FreelancerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FreelancerProfile

    user = factory.SubFactory(UserFactory)
    business_name = factory.Faker('company')
    currency = 'USD'
    default_payment_terms_days = 14
    brand_color = '#6366F1'
