"""
Promo code validation and application API endpoints.
Handles checking promo code validity and calculating discounts.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from dose.models import PromoCode
from dose.serializers import PromoCodeSerializer
from dose.services.subscription_pricing import (
    build_subscription_pricing,
    normalize_user_count,
    pricing_payload,
    promo_explanation_lines,
)

logger = logging.getLogger(__name__)


def _promo_response_payload(promo, plan_tier, user_count):
    pricing = build_subscription_pricing(plan_tier, user_count=user_count, promo_code=promo)
    return {
        'valid': True,
        'code': promo.code,
        'description': promo.description,
        'discount_type': promo.get_discount_type_display(),
        'discount_value': float(promo.discount_value),
        'discount_amount': float(pricing['promo_discount_amount']),
        'final_price': float(pricing['estimated_monthly_total']),
        'message': 'Valid',
        'promo_id': promo.id,
        'pricing': pricing_payload(pricing),
        'explanation_lines': promo_explanation_lines(promo, pricing),
    }


@csrf_exempt
@require_http_methods(["POST"])
def validate_promo_code(request):
    """
    Validate a promo code and return discount information.
    
    Request body:
    {
        "code": "EARLY",
        "plan_tier": "polysaas-1",
        "base_price": 29.99
    }
    
    Response:
    {
        "valid": true,
        "code": "EARLY",
        "description": "Early Adopter 20% discount",
        "discount_type": "percentage",
        "discount_value": 20,
        "discount_amount": 6.00,
        "final_price": 23.99,
        "message": "Valid"
    }
    or
    {
        "valid": false,
        "error": "Promo code has expired"
    }
    """
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'error': 'Invalid request body'
        }, status=400)
    
    code = data.get('code', '').strip().upper()
    plan_tier = data.get('plan_tier', 'polysaas-1')
    user_count = normalize_user_count(data.get('user_count', 1))
    
    if not code:
        return JsonResponse({
            'valid': False,
            'error': 'Promo code is required'
        }, status=400)
    
    try:
        promo = PromoCode.objects.get(code=code)
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'error': f'Promo code "{code}" not found'
        }, status=404)
    
    # Check if promo code is valid
    is_valid, message = promo.is_valid_now()
    
    if not is_valid:
        return JsonResponse({
            'valid': False,
            'error': message
        }, status=400)
    
    # Check if promo code applies to this plan
    if not promo.can_apply_to_plan(plan_tier):
        return JsonResponse({
            'valid': False,
            'error': f'Promo code "{code}" does not apply to plan "{plan_tier}"'
        }, status=400)
    
    payload = _promo_response_payload(promo, plan_tier, user_count)
    logger.info(
        'Promo code validated: %s for plan %s (%s users), discount: $%s',
        code, plan_tier, user_count, payload['discount_amount']
    )
    return JsonResponse(payload, status=200)


class PromoCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for PromoCode.
    
    Endpoints:
    - GET /api/promo-codes/ - List all active promo codes (public info only)
    - GET /api/promo-codes/validate/ - Validate a promo code
    """
    queryset = PromoCode.objects.filter(is_active=True)
    serializer_class = PromoCodeSerializer
    permission_classes = []  # Public access
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Validate a promo code via DRF endpoint.
        
        Request body:
        {
            "code": "EARLY",
            "plan_tier": "polysaas-1",
            "base_price": 29.99
        }
        """
        code = request.data.get('code', '').strip().upper()
        plan_tier = request.data.get('plan_tier', 'polysaas-1')
        user_count = normalize_user_count(request.data.get('user_count', 1))
        
        if not code:
            return Response({
                'valid': False,
                'error': 'Promo code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({
                'valid': False,
                'error': f'Promo code "{code}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if promo code is valid
        is_valid, message = promo.is_valid_now()
        
        if not is_valid:
            return Response({
                'valid': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if promo code applies to this plan
        if not promo.can_apply_to_plan(plan_tier):
            return Response({
                'valid': False,
                'error': f'Promo code "{code}" does not apply to plan "{plan_tier}"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payload = _promo_response_payload(promo, plan_tier, user_count)
        logger.info(
            'Promo code validated: %s for plan %s (%s users), discount: $%s',
            code, plan_tier, user_count, payload['discount_amount']
        )
        return Response(payload, status=status.HTTP_200_OK)
