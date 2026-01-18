from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from dose.models import Subscription, Tenant
from dose.serializers import SubscriptionSerializer
import stripe
from dose.services.osticket_tenant_provisioner import provision_osticket_tenant
from dose.services.odoo_tenant_provisioner import provision_odoo_tenant
from dose.services.suitecrm_tenant_provisioner import provision_suitecrm_tenant
from dose.services.nextcloud_tenant_provisioner import provision_nextcloud_tenant
from dose.services.dolibarr_tenant_provisioner import provision_dolibarr_tenant

stripe.api_key = 'sk_test_51S3owgPQWnaGoDqycASnxwA8ua34YdBAy1Dz0C2v2REFHgAUqXM4fJrGToWd93Kpn6YUHrKaMgimbHfPzm3yONOn00xKxopkQg'


class SubscriptionApiViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    from dose.serializers import SubscriptionCreateSerializer
    serializer_class = SubscriptionSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return self.SubscriptionCreateSerializer
        return self.serializer_class
    permission_classes = []

    def create(self, request, *args, **kwargs):
        print("SubscriptionApiViewSet.create CALLED FROM SUBSCRIPTION_VIEWS.PY")
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        try:
            logger.info("SubscriptionApiViewSet.create called")
            print(f"Request content_type: {request.content_type}")
            print(f"Parsed request data: {request.data}")
            data = request.data
            logger.info(f"Parsed data: {data}")
            tenant_name = data.get('tenant_name')
            tenant_shortname = data.get('tenant_shortname')
            token = data.get('stripe_token')
            card_name = data.get('card_name')
            tenant_id = data.get('tenant')
            logger.info(f"tenant_name={tenant_name}, token={token}, card_name={card_name}, tenant_id={tenant_id}")

            # Create user if username/email/password provided and user does not exist
            from django.contrib.auth import get_user_model
            User = get_user_model()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            print(f"[DEBUG] Received username: {username}")
            print(f"[DEBUG] Received password: {password}")
            user_obj = None
            if username and email and password:
                user_qs = User.objects.filter(username=username)
                if user_qs.exists():
                    logger.error(f"400: User {username} already exists. Subscribe is for new tenants with new users only.")
                    print(f"400: User {username} already exists. Subscribe is for new tenants with new users only.")
                    return Response({
                        'error': f'User {username} already exists. Subscribe is for new tenants with new users only.',
                        'details': {'username': username, 'email': email}
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user_obj = User.objects.create_user(username=username, email=email, password=password)
                    user_obj.is_staff = True
                    user_obj.is_superuser = True
                    user_obj.save()
                    print(f"Created new admin user: {username} (staff & superuser)")
                    # Log in the new user immediately
                    from django.contrib.auth import login
                    user_obj.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user_obj)
                    print(f"Logged in new user: {username}")

            # Always create or get tenant by name, then use its id
            if tenant_name and tenant_shortname:
                slug = tenant_shortname.lower()
                schema_name = slug.replace('-', '_')
                from dose.models import Tenant
                if Tenant.objects.filter(name=tenant_name).exists():
                    logger.error(f"400: Tenant name '{tenant_name}' already exists.")
                    print(f"400: Tenant name '{tenant_name}' already exists.")
                    return Response({'error': f"Tenant name '{tenant_name}' already exists. Please choose a different name.", 'details': {'tenant_name': tenant_name}}, status=status.HTTP_400_BAD_REQUEST)
                if Tenant.objects.filter(schema_name=schema_name).exists():
                    logger.error(f"400: Tenant schema '{schema_name}' already exists.")
                    print(f"400: Tenant schema '{schema_name}' already exists.")
                    return Response({'error': f"Tenant schema '{schema_name}' already exists. Please choose a different shortname.", 'details': {'schema_name': schema_name}}, status=status.HTTP_400_BAD_REQUEST)
                tenant_obj, created = Tenant.objects.get_or_create(
                    name=tenant_name,
                    defaults={
                        'slug': slug,
                        'schema_name': schema_name,
                        'description': 'Test tenant created for Stripe testing.'
                    }
                )
                tenant_id = tenant_obj.id

            # Assign user profile to tenant (if user and tenant exist)
            if user_obj and tenant_id:
                from dose.models import UserProfile
                try:
                    # Get existing UserProfile (created by signal handler) and update its tenant
                    user_profile = UserProfile.objects.get(user=user_obj)
                    user_profile.tenant = tenant_obj
                    user_profile.save()
                    print(f"Updated existing UserProfile for user {username} to use tenant {tenant_id}")
                except UserProfile.DoesNotExist:
                    # Fallback: create new UserProfile if somehow it doesn't exist
                    user_profile = UserProfile.objects.create(user=user_obj, tenant=tenant_obj)
                    print(f"Created new UserProfile for user {username} with tenant {tenant_id}")

                if hasattr(user_obj, 'tenant_id'):
                    user_obj.tenant_id = tenant_id
                    user_obj.save()

            # If tenant_id is still not an integer, try to convert
            try:
                tenant_id = int(tenant_id)
            except (TypeError, ValueError):
                tenant_id = None

            # For testing: skip Stripe logic if tenant_name starts with 'A'
            if tenant_name and tenant_name.lower().startswith('a'):
                sub = Subscription.objects.create(
                    tenant_id=tenant_id,
                    stripe_customer_id=None,
                    stripe_subscription_id=None,
                    card_name=card_name,
                    active=False
                )
                # Use the model serializer for the response
                from dose.serializers import SubscriptionSerializer
                serializer = SubscriptionSerializer(sub)
                logger.info("Returning test tenant subscription response")
                print("Returning test tenant subscription response")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Normal subscription/payment flow
            if not tenant_id or not token:
                logger.error(f"400 Bad Request: tenant_id={tenant_id}, token={token}, data={data}")
                logger.info("Returning 400 response for missing tenant or token")
                print("Returning 400 response for missing tenant or token")
                return Response({'error': 'Missing tenant or stripe_token', 'details': {'tenant_id': tenant_id, 'token': token, 'data': data}}, status=status.HTTP_400_BAD_REQUEST)

            # Create Stripe customer and subscription
            try:
                customer = stripe.Customer.create(
                    source=token,
                    name=card_name,
                    email=email
                )
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': getattr(settings, 'STRIPE_PRICE_ID', 'price_xxx')}],
                    trial_period_days=getattr(settings, 'STRIPE_TRIAL_PERIOD_DAYS', 14)
                )
                stripe_customer_id = customer.id
                stripe_subscription_id = subscription.id
                active = True
            except Exception as e:
                logger.error(f"Stripe error: {e}")
                print(traceback.format_exc())
                logger.error(traceback.format_exc())
                logger.info("Returning 400 response for Stripe error")
                print("Returning 400 response for Stripe error")
                return Response({'error': str(e), 'details': {'traceback': traceback.format_exc()}}, status=status.HTTP_400_BAD_REQUEST)

            # Save subscription to DB
            sub = Subscription.objects.create(
                tenant_id=tenant_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                card_name=card_name,
                active=active
            )

            # Check if OSTicket provisioning is requested
            if data.get('enable_osticket'):
                # Get tenant info for provisioning
                tenant = Tenant.objects.get(id=tenant_id)
                # Trigger OSTicket tenant provisioning
                provision_osticket_tenant.delay(
                    tenant_schema=tenant.schema_name,
                    tenant_name=tenant.name,
                    admin_email=user_obj.email if user_obj else data.get('email'),
                    company_name=tenant.name
                )

            # Check if Odoo provisioning is requested
            if data.get('enable_odoo'):
                # Get tenant info for provisioning
                tenant = Tenant.objects.get(id=tenant_id)
                # Trigger Odoo tenant provisioning
                provision_odoo_tenant.delay(
                    tenant_schema=tenant.schema_name,
                    tenant_name=tenant.name,
                    admin_email=user_obj.email if user_obj else data.get('email'),
                    company_name=tenant.name
                )

            # Check if SuiteCRM provisioning is requested
            if data.get('enable_suitecrm'):
                # Get tenant info for provisioning
                tenant = Tenant.objects.get(id=tenant_id)
                # Trigger SuiteCRM tenant provisioning
                provision_suitecrm_tenant.delay(
                    tenant_schema=tenant.schema_name,
                    tenant_name=tenant.name,
                    admin_email=user_obj.email if user_obj else data.get('email'),
                    company_name=tenant.name
                )

            # Check if Nextcloud provisioning is requested
            if data.get('enable_nextcloud'):
                # Get tenant info for provisioning
                tenant = Tenant.objects.get(id=tenant_id)
                # Trigger Nextcloud tenant provisioning
                provision_nextcloud_tenant.delay(
                    tenant_schema=tenant.schema_name,
                    tenant_name=tenant.name,
                    admin_email=user_obj.email if user_obj else data.get('email'),
                    company_name=tenant.name
                )

            # Check if Dolibarr provisioning is requested
            if data.get('enable_dolibarr'):
                # Get tenant info for provisioning
                tenant = Tenant.objects.get(id=tenant_id)
                # Trigger Dolibarr tenant provisioning
                provision_dolibarr_tenant.delay(
                    tenant_schema=tenant.schema_name,
                    tenant_name=tenant.name,
                    admin_email=user_obj.email if user_obj else data.get('email'),
                    company_name=tenant.name
                )

            # Use the model serializer for the response
            from dose.serializers import SubscriptionSerializer
            serializer = SubscriptionSerializer(sub)
            logger.info("Returning normal subscription response")
            print("Returning normal subscription response")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print('TOP-LEVEL EXCEPTION CAUGHT IN SUBSCRIPTIONAPIVIEWSET.CREATE:')
            print(traceback.format_exc())
            logger.error('TOP-LEVEL EXCEPTION CAUGHT IN SUBSCRIPTIONAPIVIEWSET.CREATE:')
            logger.error(traceback.format_exc())
            return Response({'error': str(e), 'details': {'traceback': traceback.format_exc()}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
