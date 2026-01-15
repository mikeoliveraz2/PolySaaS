# DOSE Architecture - Visual Diagrams

This document contains visual flowcharts and diagrams for the DOSE multi-tenant SaaS platform.

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Request Flow](#request-flow)
3. [Middleware Pipeline](#middleware-pipeline)
4. [OAuth Authentication Flow](#oauth-authentication-flow)
5. [External Service Passthrough](#external-service-passthrough)
6. [Multi-Tenant Architecture](#multi-tenant-architecture)
7. [Database Schema Overview](#database-schema-overview)

---

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile Browser]
    end
    
    subgraph "Authentication"
        GoogleAuth[Google OAuth2]
        GithubAuth[GitHub OAuth2]
        EmailAuth[Email/Password]
    end
    
    subgraph "Django Application - Port 8000"
        direction TB
        URLs[URL Router]
        Middleware[Middleware Pipeline]
        Views[Views Layer]
        Models[Models/ORM]
        Templates[Templates]
        Admin[Jazzmin Admin]
        UserDash[User Dashboard]
    end
    
    subgraph "External Services"
        OSTicket[OSTicket<br/>Port 8080]
        Gmail[Gmail API]
        Echo[Echo Service<br/>Port 5000]
    end
    
    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Port 5433<br/>dosedbsaas)]
    end
    
    Browser --> URLs
    Mobile --> URLs
    
    GoogleAuth -.OAuth.-> Middleware
    GithubAuth -.OAuth.-> Middleware
    EmailAuth -.Auth.-> Middleware
    
    URLs --> Middleware
    Middleware --> Views
    Views --> Models
    Models --> PostgreSQL
    Views --> Templates
    Templates --> Admin
    Templates --> UserDash
    
    Middleware -.Proxy.-> OSTicket
    Views -.API.-> Gmail
    Middleware -.Proxy.-> Echo
    
    style Browser fill:#e1f5ff
    style Admin fill:#ffe1e1
    style UserDash fill:#e1ffe1
    style PostgreSQL fill:#fff3cd
    style OSTicket fill:#f8d7da
    style Gmail fill:#f8d7da
```

---

## Request Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant M as Middleware Pipeline
    participant V as Views
    participant DB as PostgreSQL
    participant E as External Service
    
    B->>M: HTTP Request
    activate M
    
    M->>M: 1. Security Check
    M->>M: 2. Session Processing
    M->>M: 3. CSRF Validation
    M->>M: 4. Authentication
    M->>M: 5. Tenant Resolution
    
    alt External Service Request
        M->>E: Forward Request (NO IFRAME)
        E->>M: HTML Response
        M->>M: Rewrite URLs
        M->>B: Modified HTML
    else Django View Request
        M->>V: Route to View
        activate V
        V->>DB: Query with Tenant Filter
        DB->>V: Data
        V->>V: Render Template
        V->>M: HTML Response
        deactivate V
        M->>M: Response Processing
        M->>B: Final Response
    end
    
    deactivate M
```

---

## Middleware Pipeline

```mermaid
graph TB
    Start[Incoming Request] --> M1[1. SecurityMiddleware]
    M1 --> M2[2. DebugSessionMiddleware]
    M2 --> M3[3. CommonMiddleware]
    M3 --> M4[4. CsrfViewMiddleware]
    M4 --> M5[5. SessionMiddleware]
    M5 --> M6[6. AuthenticationMiddleware]
    M6 --> M7[7. UserRequestTracking]
    M7 --> M8[8. DebugRequestMiddleware]
    M8 --> M9[9. AdminUnauthorizedMiddleware]
    M9 --> M10[10. AdminTenantSession]
    M10 --> M11[11. SessionTenantMiddleware ⭐]
    M11 --> M12[12. MessagesMiddleware]
    M12 --> M13[13. AccountMiddleware]
    M13 --> M14[14. DoseRequestController ⭐]
    M14 --> M15[15. ExternalPassthrough ⭐]
    M15 --> Decision{External<br/>Service?}
    
    Decision -->|Yes| Proxy[Proxy to External]
    Decision -->|No| M16[16. JazzminTenantTheme]
    
    Proxy --> Response1[Return Modified HTML]
    
    M16 --> View[Django View Processing]
    View --> M17[17. DoseResponseController ⭐]
    M17 --> M18[18. XFrameOptions]
    M18 --> Response2[Return Response]
    
    style M11 fill:#ffe1e1
    style M14 fill:#ffe1e1
    style M15 fill:#ffe1e1
    style M17 fill:#ffe1e1
    style Decision fill:#fff3cd
```

---

## OAuth Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant D as Django/Allauth
    participant G as Google OAuth
    participant DB as Database
    
    U->>B: Click "Sign in with Google"
    B->>D: GET /accounts/google/login/
    D->>G: Redirect to consent screen
    G->>U: Show authorization prompt
    U->>G: Approve access
    G->>D: Callback with auth code
    D->>G: Exchange code for token
    G->>D: Access token + ID token
    D->>DB: Create/Update SocialAccount
    D->>DB: Create/Link User
    D->>DB: Store OAuth tokens
    
    alt User is Staff
        D->>B: Redirect to /admin/
        B->>U: Show Jazzmin Admin
    else Regular User
        D->>B: Redirect to /user-dashboard/
        B->>U: Show User Dashboard
    end
```

---

## External Service Passthrough (NO IFRAME)

```mermaid
graph TB
    subgraph "Browser"
        UserClick[User clicks OSTicket link]
    end
    
    subgraph "Django - ExternalPassthroughMiddleware"
        Intercept[Intercept Request<br/>/admin/osticket/login.php]
        Match{Matches<br/>trigger_path?}
        Forward[Forward to External URL<br/>http://localhost:8080/login.php]
        Receive[Receive HTML Response]
        Rewrite[Rewrite URLs in HTML<br/>Forms, Links, Scripts, CSS]
        Return[Return Modified HTML]
    end
    
    subgraph "External Service"
        OSTicket[OSTicket Application<br/>Port 8080]
    end
    
    UserClick --> Intercept
    Intercept --> Match
    Match -->|Yes| Forward
    Match -->|No| Django[Continue to Django View]
    Forward --> OSTicket
    OSTicket --> Receive
    Receive --> Rewrite
    Rewrite --> Return
    Return --> Browser[Browser renders as<br/>native Django page]
    
    style Rewrite fill:#ffe1e1
    style Return fill:#e1ffe1
    style Browser fill:#e1f5ff
```

### URL Rewriting Example

```mermaid
graph LR
    subgraph "Original HTML from OSTicket"
        O1["&lt;form action='/scp/login.php'&gt;"]
        O2["&lt;link href='/css/style.css'&gt;"]
        O3["&lt;a href='/scp/tickets.php'&gt;"]
    end
    
    subgraph "Middleware Rewriting"
        R[URL Rewriter]
    end
    
    subgraph "Modified HTML to Browser"
        M1["&lt;form action='/admin/osticket/scp/login.php'&gt;"]
        M2["&lt;link href='/admin/osticket/css/style.css'&gt;"]
        M3["&lt;a href='/admin/osticket/scp/tickets.php'&gt;"]
    end
    
    O1 --> R
    O2 --> R
    O3 --> R
    R --> M1
    R --> M2
    R --> M3
    
    style R fill:#ffe1e1
```

---

## Multi-Tenant Architecture

```mermaid
graph TB
    subgraph "User Session"
        User[Logged in User]
        Session[Session Storage]
        TenantID[Tenant ID in Session]
    end
    
    subgraph "SessionTenantMiddleware"
        Extract[Extract Tenant ID<br/>from Session]
        SetContext[Set request.tenant]
        Filter[Apply to all<br/>QuerySets]
    end
    
    subgraph "Django ORM"
        QuerySet[Model.objects.all]
        AutoFilter[Automatic Tenant<br/>Filtering]
    end
    
    subgraph "Database"
        direction TB
        AllData[(All Tenant Data<br/>Single Database)]
        Tenant1[Tenant 1 Data]
        Tenant2[Tenant 2 Data]
        Tenant3[Tenant 3 Data]
    end
    
    User --> Session
    Session --> TenantID
    TenantID --> Extract
    Extract --> SetContext
    SetContext --> Filter
    Filter --> QuerySet
    QuerySet --> AutoFilter
    AutoFilter --> AllData
    AllData -.Filter tenant_id=1.-> Tenant1
    AllData -.Filter tenant_id=2.-> Tenant2
    AllData -.Filter tenant_id=3.-> Tenant3
    
    style Extract fill:#ffe1e1
    style AutoFilter fill:#ffe1e1
    style Tenant1 fill:#e1ffe1
```

---

## Database Schema Overview

```mermaid
erDiagram
    User ||--o{ UserProfile : has
    User ||--o{ SocialAccount : has
    User }o--o{ Tenant : "belongs to"
    
    Tenant ||--o{ Domain : has
    Tenant ||--o{ TenantTheme : has
    Tenant ||--o{ PassthroughEndpoint : configures
    
    SocialAccount ||--o{ SocialToken : has
    SocialAccount }o--|| SocialApp : uses
    
    PassthroughEndpoint {
        string trigger_path
        string endpoint_url
        boolean is_enabled
        boolean show_in_menu
        string menu_title
    }
    
    UserProfile {
        string light_theme
        string dark_theme
        boolean use_system_pref
    }
    
    Tenant {
        string name
        string schema_name
        boolean is_active
    }
    
    SocialApp {
        string provider
        string client_id
        string secret
    }
    
    SocialToken {
        string token
        string token_secret
        datetime expires_at
    }
```

---

## Application Layer Structure

```mermaid
graph TB
    subgraph "Django Project"
        direction TB
        
        subgraph "mysite (Project Config)"
            Settings[settings.py]
            URLs[urls.py]
            WSGI[wsgi.py]
            MW1[Middleware Modules]
        end
        
        subgraph "dose (Main App)"
            DoseModels[models.py]
            DoseViews[views.py]
            DoseAdmin[admin.py]
            DoseTemplates[templates/]
            DoseMiddleware[middleware/]
        end
        
        subgraph "parameters (Service Params)"
            ParamModels[models.py]
            ParamViews[views.py]
            ParamAPI[API ViewSets]
        end
        
        subgraph "Third-Party Apps"
            Jazzmin[jazzmin]
            Allauth[django-allauth]
            DRF[rest_framework]
        end
    end
    
    Settings --> DoseModels
    URLs --> DoseViews
    MW1 --> DoseMiddleware
    DoseViews --> DoseTemplates
    
    Jazzmin -.themes.-> DoseAdmin
    Allauth -.auth.-> DoseViews
    DRF -.api.-> ParamAPI
```

---

## Smart Login Redirect Logic

```mermaid
flowchart TD
    Start[User Accesses /] --> CheckAuth{User<br/>Authenticated?}
    CheckAuth -->|No| Login[Redirect to<br/>/accounts/login/]
    CheckAuth -->|Yes| CheckStaff{is_staff or<br/>is_superuser?}
    
    Login --> LoginPage[Login Page<br/>3 Options]
    LoginPage --> Google[Google OAuth]
    LoginPage --> GitHub[GitHub OAuth]
    LoginPage --> Email[Email/Password]
    
    Google --> OAuth[OAuth Flow]
    GitHub --> OAuth
    Email --> DjangoAuth[Django Auth]
    
    OAuth --> Success{Success?}
    DjangoAuth --> Success
    
    Success -->|Yes| CheckStaff
    Success -->|No| Login
    
    CheckStaff -->|Yes| AdminDash[/admin/<br/>Jazzmin Interface]
    CheckStaff -->|No| UserDash[/user-dashboard/<br/>AdminLTE Interface]
    
    AdminDash --> Features1[• Tenant Management<br/>• OSTicket Link<br/>• Gmail Link<br/>• Full Admin Tools]
    UserDash --> Features2[• Personal Dashboard<br/>• Service Links<br/>• Profile<br/>• Notifications]
    
    style CheckStaff fill:#fff3cd
    style AdminDash fill:#ffe1e1
    style UserDash fill:#e1ffe1
```

---

## Dynamic Menu Injection

```mermaid
graph TB
    subgraph "Database"
        PE[(PassthroughEndpoint)]
        PE1[OSTicket<br/>show_in_menu=True]
        PE2[Gmail<br/>show_in_menu=True]
        PE3[Echo<br/>show_in_menu=False]
    end
    
    subgraph "Context Processor"
        Query[Query Enabled<br/>Menu Endpoints]
        Filter[Filter show_in_menu=True]
        Context[Add to Template Context]
    end
    
    subgraph "Templates"
        AdminMenu[Admin Top Menu]
        UserMenu[User Top Menu]
        Sidebar[User Sidebar]
        Banner[Tenant Banner]
        QuickActions[Quick Actions]
    end
    
    PE --> PE1
    PE --> PE2
    PE --> PE3
    
    PE1 --> Query
    PE2 --> Query
    PE3 -.excluded.-> Query
    
    Query --> Filter
    Filter --> Context
    
    Context --> AdminMenu
    Context --> UserMenu
    Context --> Sidebar
    Context --> Banner
    Context --> QuickActions
    
    style Filter fill:#ffe1e1
    style Context fill:#e1ffe1
```

---

## View this in GitHub

These diagrams use Mermaid syntax, which renders automatically on:
- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Many markdown viewers

For the best experience, view this file on GitHub or use a Mermaid-compatible viewer.

## Legend

- 🔴 Red/Pink = Critical Components
- 🟢 Green = User-Facing
- 🟡 Yellow = Decision Points
- ⭐ = Key Features
- Solid lines = Direct flow
- Dotted lines = Async/OAuth/External

