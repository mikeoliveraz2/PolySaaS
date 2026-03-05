# PolySaaS Dataflow Diagram

## System-Wide Dataflow

```mermaid
flowchart TB
    subgraph Clients["Client Tier"]
        Browser["Browser / Admin Portal"]
        ChromeExt["PolySniffer Chrome Extension"]
        MattClient["Mattermost Client"]
        APIClient["REST API Consumer"]
    end

    subgraph Django["Django DOSE — Application Tier"]
        direction TB

        subgraph MW["Middleware Pipeline"]
            direction TB
            Security["SecurityMiddleware"]
            Session["SessionMiddleware"]
            Auth["AuthenticationMiddleware"]
            Tracking["UserRequestTrackingMiddleware"]
            TenantMW["SessionTenantMiddleware\n(SET search_path)"]
            ReqCtrl["DoseRequestController\n(Event Matching)"]
            JazzTheme["JazzminTenantThemeMiddleware"]
            RespCtrl["DoseResponseController\n(Callbacks)"]
            PassMW["ExternalPassthroughMiddleware"]
        end

        subgraph Views["View Layer"]
            Landing["Landing / Dashboard Views"]
            RESTAPI["REST API ViewSets\n(16+ endpoints)"]
            SnifferViews["PolySniffer Views"]
            PassViews["Passthrough Views"]
            AdminViews["Admin Views\n(Jazzmin Portal)"]
        end

        subgraph Services["Service Layer"]
            Orchestration["Orchestration Engine\n(Instructions / Tasks)"]
            SnifferEngine["PolySniffer Engine\n(Capture / AI Analysis)"]
            PassEngine["Passthrough Engine\n(Proxy / Iframe)"]
            MQRouter["MQ Router\n(Adapters)"]
        end
    end

    subgraph Async["Async Processing"]
        Celery["Celery Workers"]
        RabbitMQ["RabbitMQ Broker"]
        Redis["Redis Cache"]
    end

    subgraph Data["Data Tier"]
        subgraph PG["PostgreSQL :5433"]
            Public["public schema\n(shared tables)"]
            Olient["olient schema"]
            Demo["demo schema"]
            TenantN["tenant_N schema"]
        end
    end

    subgraph SaaS["Bundled SaaS Applications"]
        Odoo["Odoo :8069"]
        Nextcloud["Nextcloud :8888"]
        Mattermost["Mattermost :8065"]
        WordPress["WordPress :8980"]
        Liferay["Liferay CE :8181"]
        Dolibarr["Dolibarr :8889"]
        PSM["PolySysMon :9001"]
    end

    subgraph Cloud["GCP Production"]
        CloudRun["Cloud Run"]
        CloudSQL["Cloud SQL"]
        GCS["Cloud Storage"]
        PubSub["Pub/Sub"]
        SecretMgr["Secret Manager"]
    end

    %% Client → Django flows
    Browser -->|"HTTP/HTTPS"| MW
    ChromeExt -->|"POST /silent-capture"| SnifferViews
    MattClient -->|"Mattermost API"| Mattermost
    APIClient -->|"REST JSON"| RESTAPI

    %% Middleware pipeline
    Security --> Session --> Auth --> Tracking --> TenantMW --> ReqCtrl --> JazzTheme --> RespCtrl --> PassMW

    %% Middleware → Views
    MW --> Views

    %% Views → Services
    Landing --> Orchestration
    RESTAPI --> Orchestration
    SnifferViews --> SnifferEngine
    PassViews --> PassEngine
    AdminViews --> Landing

    %% Services → Data
    Orchestration -->|"ORM Queries\n(schema-scoped)"| PG
    SnifferEngine -->|"TrafficLog writes"| PG
    PassEngine -->|"Config reads"| PG

    %% Services → Async
    Orchestration -->|"Task dispatch"| Celery
    Celery <-->|"Broker"| RabbitMQ
    Celery -->|"Results"| PG
    MQRouter <-->|"Messages"| RabbitMQ

    %% Services → SaaS
    PassEngine -->|"Proxy / API"| Odoo
    PassEngine -->|"Proxy / API"| Nextcloud
    PassEngine -->|"Proxy / API"| Mattermost
    PassEngine -->|"Proxy / API"| WordPress
    PassEngine -->|"Proxy / API"| Liferay
    PassEngine -->|"Proxy / API"| Dolibarr
    PassEngine -->|"Proxy / API"| PSM

    %% PolySniffer captures from SaaS
    SnifferEngine -.->|"Capture traffic"| SaaS

    %% Production deployment
    Django -.->|"Deploys to"| CloudRun
    PG -.->|"Prod equivalent"| CloudSQL
    MQRouter -.->|"Prod adapter"| PubSub
    Django -.->|"Static/Media"| GCS
    Django -.->|"Secrets"| SecretMgr

    %% Styling
    classDef client fill:#4A90D9,stroke:#2C5F8A,color:#fff
    classDef django fill:#2ECC71,stroke:#1A9C50,color:#fff
    classDef async fill:#F39C12,stroke:#C87F0A,color:#fff
    classDef data fill:#9B59B6,stroke:#7D3C98,color:#fff
    classDef saas fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef cloud fill:#1ABC9C,stroke:#148F77,color:#fff

    class Browser,ChromeExt,MattClient,APIClient client
    class Celery,RabbitMQ,Redis async
    class Public,Olient,Demo,TenantN data
    class Odoo,Nextcloud,Mattermost,WordPress,Liferay,Dolibarr,PSM saas
    class CloudRun,CloudSQL,GCS,PubSub,SecretMgr cloud
```

---

## Request Lifecycle Dataflow

```mermaid
sequenceDiagram
    participant B as Browser
    participant MW as Middleware Pipeline
    participant TC as TenantMiddleware
    participant RC as DoseRequestController
    participant V as View / API
    participant DB as PostgreSQL
    participant MQ as Message Queue
    participant SaaS as SaaS App
    participant Resp as DoseResponseController

    B->>MW: HTTP Request
    MW->>MW: Security → Session → Auth
    MW->>TC: Set tenant from session
    TC->>DB: SET search_path TO tenant,public
    TC->>RC: Pass request

    alt Instruction Match Found
        RC->>DB: Query Instructions by eventKey
        RC->>MQ: Publish to matched queue
        RC->>V: Forward with orchestration context
    else No Match
        RC->>V: Forward unchanged
    end

    alt Passthrough Request (/pt/ or /dose/passthrough/)
        V->>SaaS: Proxy request
        SaaS-->>V: SaaS response
    else Standard View
        V->>DB: Query tenant-scoped data
        DB-->>V: Results
    end

    V-->>Resp: Response
    Resp->>DB: Log CallBackData (if configured)
    Resp-->>B: HTTP Response
```

---

## PolySniffer Capture Flow

```mermaid
sequenceDiagram
    participant CE as Chrome Extension
    participant BG as background.js
    participant CS as content.js
    participant D as Django PolySniffer
    participant DB as PostgreSQL
    participant AI as AI Analysis

    CE->>BG: User clicks "Start Capture"
    BG->>BG: Enable webRequest listener

    loop For each HTTP request
        BG->>BG: shouldCapture() check
        BG->>BG: Classify request (Odoo RPC, REST, etc.)
        BG->>CS: Capture request details
        CS->>CS: Intercept fetch/XHR, forms, cookies
        CS-->>BG: Captured data
    end

    CE->>BG: User clicks "Send Batch"
    BG->>D: POST /admin/polysniffer/silent-capture/<id>/
    D->>DB: Store TrafficLog with HAR data
    D-->>BG: Capture confirmed

    opt AI Analysis
        D->>AI: POST /admin/polysniffer/ai-analyze/<id>/
        AI-->>D: Endpoint analysis + handler code
    end
```

---

## Multi-Tenant Data Isolation

```mermaid
flowchart LR
    subgraph Request["Incoming Request"]
        User["User with session\ntenant_id=olient"]
    end

    subgraph MW["SessionTenantMiddleware"]
        Lookup["Lookup Tenant\nby session tenant_id"]
        SetPath["SET search_path TO\nolient, public"]
    end

    subgraph PG["PostgreSQL"]
        direction TB
        Public["public schema\n• auth_user\n• dose_tenant\n• dose_userprofile"]
        Olient["olient schema\n• dose_instruction\n• dose_task\n• dose_dashboardbutton\n• dose_navigationpanel"]
        Demo["demo schema\n• dose_instruction\n• dose_task\n• dose_dashboardbutton\n• dose_navigationpanel"]
    end

    User --> Lookup --> SetPath
    SetPath -->|"ORM queries hit\nolient first,\nthen public"| Olient
    SetPath -.->|"Shared tables\nalways visible"| Public
    Demo -.->|"Invisible to\nthis request"| Demo

    style Olient fill:#2ECC71,stroke:#1A9C50,color:#fff
    style Public fill:#3498DB,stroke:#2C80B4,color:#fff
    style Demo fill:#95A5A6,stroke:#7F8C8D,color:#fff
```

---

*Diagrams rendered with Mermaid. View in any Mermaid-compatible viewer or GitHub.*
