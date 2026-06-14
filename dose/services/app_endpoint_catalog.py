"""
Catalog of bundled application API endpoints and entity mappings.
Used by EndpointDataExtractor to identify what entity is being
created/updated and how to normalize the data for cross-app sync.

Topic naming convention: polysaas.{app}.{entity}.{action}
  e.g., polysaas.dolibarr.customer.created
        polysaas.odoo.partner.updated
"""

APP_ENDPOINT_CATALOG = {
    "dolibarr": {
        "base_port": 8889,
        "api_prefix": "/api/index.php",
        "entities": {
            "customer": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/index.php/thirdparties",
                    "topic": "polysaas.dolibarr.customer.created",
                    "field_map": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "address": "address",
                        "zip": "zip",
                        "town": "town",
                        "country_code": "country_code",
                        "client": "customer_type",
                        "code_client": "customer_code",
                    }
                },
                "update": {
                    "method": "PUT",
                    "path_pattern": "/api/index.php/thirdparties/",
                    "topic": "polysaas.dolibarr.customer.updated",
                    "field_map": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "address": "address",
                        "zip": "zip",
                        "town": "town",
                        "country_code": "country_code",
                    }
                },
            },
            "invoice": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/index.php/invoices",
                    "topic": "polysaas.dolibarr.invoice.created",
                    "field_map": {
                        "socid": "customer_id",
                        "date": "invoice_date",
                        "total_ttc": "total_amount",
                        "ref": "reference",
                    }
                },
            },
            "contact": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/index.php/contacts",
                    "topic": "polysaas.dolibarr.contact.created",
                    "field_map": {
                        "firstname": "first_name",
                        "lastname": "last_name",
                        "email": "email",
                        "phone_pro": "phone",
                        "socid": "company_id",
                    }
                },
            },
        },
    },

    "odoo": {
        "base_port": 8069,
        "api_prefix": "/web/dataset",
        "entities": {
            "partner": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/web/dataset/call_kw/res.partner/create",
                    "topic": "polysaas.odoo.partner.created",
                    "field_map": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "street": "address",
                        "zip": "zip",
                        "city": "town",
                        "country_id": "country_code",
                        "customer_rank": "customer_type",
                    }
                },
                "update": {
                    "method": "POST",
                    "path_pattern": "/web/dataset/call_kw/res.partner/write",
                    "topic": "polysaas.odoo.partner.updated",
                    "field_map": {
                        "name": "name",
                        "email": "email",
                        "phone": "phone",
                        "street": "address",
                        "zip": "zip",
                        "city": "town",
                    }
                },
            },
            "invoice": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/web/dataset/call_kw/account.move/create",
                    "topic": "polysaas.odoo.invoice.created",
                    "field_map": {
                        "partner_id": "customer_id",
                        "invoice_date": "invoice_date",
                        "amount_total": "total_amount",
                        "name": "reference",
                    }
                },
            },
        },
    },

    "nextcloud": {
        "base_port": 8888,
        "api_prefix": "/ocs/v2.php",
        "entities": {
            "user": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/ocs/v2.php/cloud/users",
                    "topic": "polysaas.nextcloud.user.created",
                    "field_map": {
                        "userid": "username",
                        "displayName": "name",
                        "email": "email",
                        "groups": "groups",
                    }
                },
            },
            "share": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/ocs/v2.php/apps/files_sharing/api/v1/shares",
                    "topic": "polysaas.nextcloud.share.created",
                    "field_map": {
                        "path": "file_path",
                        "shareWith": "shared_with",
                        "shareType": "share_type",
                        "permissions": "permissions",
                    }
                },
            },
        },
    },

    "mattermost": {
        "base_port": 8065,
        "api_prefix": "/api/v4",
        "entities": {
            "user": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/v4/users",
                    "topic": "polysaas.mattermost.user.created",
                    "field_map": {
                        "username": "username",
                        "email": "email",
                        "first_name": "first_name",
                        "last_name": "last_name",
                    }
                },
            },
            "post": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/v4/posts",
                    "topic": "polysaas.mattermost.post.created",
                    "field_map": {
                        "channel_id": "channel_id",
                        "message": "message",
                        "user_id": "user_id",
                    }
                },
            },
            "channel": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/api/v4/channels",
                    "topic": "polysaas.mattermost.channel.created",
                    "field_map": {
                        "name": "name",
                        "display_name": "display_name",
                        "type": "channel_type",
                        "team_id": "team_id",
                    }
                },
            },
        },
    },

    "wordpress": {
        "base_port": 8980,
        "api_prefix": "/wp-json/wp/v2",
        "entities": {
            "post": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/wp-json/wp/v2/posts",
                    "topic": "polysaas.wordpress.post.created",
                    "field_map": {
                        "title": "title",
                        "content": "content",
                        "status": "status",
                        "author": "author_id",
                    }
                },
            },
            "user": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/wp-json/wp/v2/users",
                    "topic": "polysaas.wordpress.user.created",
                    "field_map": {
                        "username": "username",
                        "email": "email",
                        "name": "name",
                        "roles": "roles",
                    }
                },
            },
        },
    },

    "liferay": {
        "base_port": 8181,
        "api_prefix": "/o/headless-admin-user/v1.0",
        "entities": {
            "user": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/o/headless-admin-user/v1.0/user-accounts",
                    "topic": "polysaas.liferay.user.created",
                    "field_map": {
                        "emailAddress": "email",
                        "givenName": "first_name",
                        "familyName": "last_name",
                        "screenName": "username",
                    }
                },
            },
            "site": {
                "create": {
                    "method": "POST",
                    "path_pattern": "/o/headless-admin-user/v1.0/sites",
                    "topic": "polysaas.liferay.site.created",
                    "field_map": {
                        "name": "name",
                        "description": "description",
                    }
                },
            },
        },
    },
}


def match_endpoint(request_path, request_method):
    """
    Match a request path and method against the catalog.
    Returns (app_name, entity_name, action, config) or (None, None, None, None).
    """
    request_path = request_path.rstrip('/')
    request_method = request_method.upper()

    for app_name, app_config in APP_ENDPOINT_CATALOG.items():
        for entity_name, entity_config in app_config["entities"].items():
            for action, action_config in entity_config.items():
                if action_config["method"] != request_method:
                    continue
                pattern = action_config["path_pattern"].rstrip('/')
                if pattern in request_path or request_path.endswith(pattern):
                    return app_name, entity_name, action, action_config
    return None, None, None, None


def normalize_data(raw_data, field_map):
    """
    Normalize raw app-specific data using the field map.
    Returns a dict with canonical field names.
    """
    normalized = {}
    for app_field, canonical_field in field_map.items():
        if app_field in raw_data:
            normalized[canonical_field] = raw_data[app_field]
    return normalized


def get_all_topics():
    """Return a flat list of all Pub/Sub topics defined in the catalog."""
    topics = []
    for app_config in APP_ENDPOINT_CATALOG.values():
        for entity_config in app_config["entities"].values():
            for action_config in entity_config.values():
                topics.append(action_config["topic"])
    return topics
