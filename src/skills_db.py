"""
skills_db.py
------------
Central skills knowledge base used by:
  - EntityRuler (for guaranteed exact-match extraction)
  - Skill normalizer / RapidFuzz scorer (for alias deduplication)

CANONICAL_SKILLS: flat list of known tech skills fed into spaCy EntityRuler.
SKILL_ALIASES: maps every known alias/variant -> canonical name.
"""

# ── Canonical skills list (fed into spaCy EntityRuler) ─────────────────────
# Each entry becomes a pattern that is ALWAYS labelled SKILL regardless of
# what the neural NER layer predicts.
CANONICAL_SKILLS: list[str] = [
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go",
    "Golang", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "MATLAB", "Perl", "Haskell", "Elixir", "Erlang", "Dart", "Lua",
    "Groovy", "Shell", "Bash", "PowerShell", "Assembly", "COBOL", "Fortran",
    "Visual Basic", "VBA", "Objective-C", "F#",

    # Web Frameworks
    "React", "React.js", "ReactJS", "Angular", "AngularJS", "Vue",
    "Vue.js", "VueJS", "Next.js", "Nuxt.js", "Svelte", "Ember.js",
    "Backbone.js", "jQuery", "Bootstrap", "Tailwind CSS", "SASS", "LESS",
    "Django", "Flask", "FastAPI", "Express", "Express.js", "Node.js",
    "NestJS", "Spring", "Spring Boot", "Laravel", "Rails", "Ruby on Rails",
    "ASP.NET", ".NET", ".NET Core", "Blazor", "Gin", "Echo", "Fiber",
    "Tornado", "Pyramid", "Falcon", "Starlette",

    # Databases
    "MySQL", "PostgreSQL", "Postgres", "SQLite", "Oracle", "SQL Server",
    "MSSQL", "MariaDB", "MongoDB", "Redis", "Cassandra", "DynamoDB",
    "Elasticsearch", "Neo4j", "CouchDB", "InfluxDB", "Firebase",
    "Firestore", "Supabase", "PlanetScale", "Fauna", "RethinkDB",
    "HBase", "BigTable", "Cosmos DB", "Aurora", "Redshift", "BigQuery",
    "Snowflake", "Databricks", "Hive", "Presto", "Trino",

    # Cloud & DevOps
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP",
    "Google Cloud", "Google Cloud Platform", "DigitalOcean", "Heroku",
    "Vercel", "Netlify", "Cloudflare",
    "Docker", "Kubernetes", "K8s", "Helm", "Terraform", "Ansible",
    "Puppet", "Chef", "Jenkins", "GitHub Actions", "GitLab CI",
    "CircleCI", "Travis CI", "ArgoCD", "Flux", "Pulumi",
    "EC2", "S3", "Lambda", "ECS", "EKS", "CloudFormation", "CDK",
    "IAM", "VPC", "CloudWatch", "SQS", "SNS", "API Gateway",
    "Azure DevOps", "Azure Functions", "Azure Blob Storage",
    "GKE", "Cloud Run", "Cloud Functions", "Pub/Sub", "Cloud Storage",

    # Data Science & ML
    "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing",
    "Computer Vision", "Reinforcement Learning", "Transfer Learning",
    "PyTorch", "TensorFlow", "Keras", "scikit-learn", "sklearn",
    "XGBoost", "LightGBM", "CatBoost", "Hugging Face", "Transformers",
    "BERT", "GPT", "LLaMA", "spaCy", "NLTK", "Gensim", "FastText",
    "OpenCV", "Pillow", "NumPy", "Pandas", "SciPy", "Matplotlib",
    "Seaborn", "Plotly", "Bokeh", "Dash", "Streamlit", "Gradio",
    "Jupyter", "Jupyter Notebook", "JupyterLab",
    "MLflow", "DVC", "Weights & Biases", "W&B", "Optuna", "Ray",
    "Apache Spark", "PySpark", "Dask", "Airflow", "Prefect", "Dagster",
    "Kafka", "RabbitMQ", "Celery", "Luigi",
    "ONNX", "TensorRT", "CoreML", "OpenAI API",

    # Generative AI & Large Language Models
    "Generative AI", "Large Language Models", "LLM", "LLMs", "RAG",
    "Retrieval-Augmented Generation", "LangChain", "LlamaIndex",
    "LangGraph", "DSPy", "Vector Databases", "ChromaDB", "Pinecone",
    "Milvus", "Qdrant", "Weaviate", "MLOps", "Model Deployment",
    "Prompt Engineering", "Semantic Search",

    # Modern AI Inference & Fine-Tuning
    "vLLM", "Ollama", "LoRA", "QLoRA", "Axolotl", "LangSmith",
    "Instructor", "Mistral", "Claude API", "Gemini API", "OpenAI API",
    "Llama", "LLaMA", "LLaMA 2", "LLaMA 3", "Phi", "Falcon", "Mixtral",
    "PEFT", "DeepSpeed", "FlashAttention", "bitsandbytes",
    "Anthropic", "Cohere", "Together AI", "Replicate",
    "Guardrails AI", "LiteLLM", "Outlines",

    # Core CS & Domains
    "Computer Science", "Artificial Intelligence", "AI", "Data Analytics",
    "Data Analysis", "IT Integration", "Workflow Orchestration",

    # Data Engineering
    "ETL", "ELT", "Data Warehousing", "Data Lake", "Data Pipeline",
    "dbt", "dbt Core", "Fivetran", "Stitch", "Airbyte", "Informatica",
    "Great Expectations", "Delta Lake", "Apache Iceberg", "Apache Flink",
    "OpenMetadata", "Apache Hudi", "Trino", "Apache Druid",
    "Tableau", "Power BI", "Looker", "Metabase", "Grafana", "Kibana",

    # Version Control & Tooling
    "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
    "Linux", "Unix", "macOS", "Windows Server", "Ubuntu", "CentOS",
    "Nginx", "Apache", "Caddy", "HAProxy", "Traefik",
    "REST", "REST API", "RESTful", "GraphQL", "gRPC", "WebSockets",
    "SOAP", "OpenAPI", "Swagger", "Postman", "Insomnia",
    "Makefile", "CMake", "Bazel", "Gradle", "Maven", "npm", "pnpm", "yarn",
    "pre-commit", "Ruff", "Black", "ESLint", "Prettier",

    # Security
    "OAuth", "OAuth2", "JWT", "SAML", "OpenID Connect", "SSL", "TLS",
    "HTTPS", "PKI", "Penetration Testing", "OWASP", "SIEM",
    "Splunk", "CrowdStrike", "Wireshark", "Nmap", "Metasploit",
    "Vault", "HashiCorp Vault", "Secrets Manager",

    # Mobile
    "Android", "iOS", "React Native", "Flutter", "Xamarin",
    "SwiftUI", "Jetpack Compose", "Ionic", "Cordova", "Capacitor",

    # Testing
    "Jest", "Pytest", "unittest", "Selenium", "Cypress", "Playwright",
    "JUnit", "TestNG", "Mocha", "Chai", "RSpec", "PHPUnit",
    "Postman", "LoadRunner", "JMeter", "Locust",

    # Project Management / Methodology
    "Agile", "Scrum", "Kanban", "Jira", "Confluence", "Trello",
    "Notion", "Asana", "Monday.com", "Linear", "Figma", "Miro",

    # System Design & Architecture Concepts
    "CI/CD", "DevOps", "SRE", "Site Reliability Engineering",
    "Microservices", "Event-Driven Architecture", "Domain-Driven Design",
    "System Design", "API Design", "Database Design",
    "Load Balancing", "Caching", "Rate Limiting", "Message Queues",
    "Distributed Systems", "High Availability", "Fault Tolerance",
    "Scalability", "Observability", "Service Mesh", "Istio",
    "API Gateway", "BFF", "CQRS", "Event Sourcing", "Saga Pattern",

    # Languages (extended)
    "Zig", "Nim", "Crystal", "Mojo", "Solidity", "Move",

    # Soft / Leadership Skills (structured — LLM scores quality)
    "Team Leadership", "Technical Mentoring", "Cross-functional Collaboration",
    "Stakeholder Management", "Technical Writing", "Code Review",
    "Project Management", "Product Thinking",

    # Cloud certifications as skills
    "AWS Certified", "GCP Certified", "Azure Certified",
    "CKA", "CKAD", "CKS", "PMP", "Terraform Associate",
]

# ── Alias Normalization Map ─────────────────────────────────────────────────
# alias (lowercased) -> canonical name (proper case as in a resume)
SKILL_ALIASES: dict[str, str] = {
    # Python variants
    "python3": "Python",
    "python 3": "Python",
    "py": "Python",

    # JavaScript variants
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ecmascript": "JavaScript",
    "es6": "JavaScript",
    "es2015": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",

    # React variants
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",

    # Angular variants
    "angular": "Angular",
    "angularjs": "Angular",
    "angular.js": "Angular",
    "angular js": "Angular",
    "angular 2+": "Angular",

    # Vue variants
    "vue": "Vue",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "vue js": "Vue",

    # Node.js variants
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",

    # Django variants
    "django rest framework": "Django",
    "drf": "Django",

    # Next.js variants
    "next": "Next.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",

    # PostgreSQL variants
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "pg": "PostgreSQL",

    # MongoDB variants
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",

    # .NET variants
    ".net": ".NET",
    "dotnet": ".NET",
    "dot net": ".NET",
    ".net core": ".NET Core",
    "asp.net": "ASP.NET",
    "asp.net core": "ASP.NET",

    # AWS variants
    "aws": "AWS",
    "amazon web services": "AWS",
    "amazon aws": "AWS",

    # GCP variants
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",

    # Kubernetes variants
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "kube": "Kubernetes",

    # Machine Learning variants
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",

    # Deep Learning variants
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",

    # NLP variants
    "nlp": "NLP",
    "natural language processing": "NLP",
    "text mining": "NLP",

    # C++ variants
    "c++": "C++",
    "cpp": "C++",
    "c plus plus": "C++",

    # C# variants
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",

    # Go variants
    "go": "Go",
    "golang": "Go",

    # scikit-learn variants
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",

    # PyTorch variants
    "pytorch": "PyTorch",
    "torch": "PyTorch",

    # TensorFlow variants
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",

    # spaCy variants
    "spacy": "spaCy",

    # Flutter variants
    "flutter": "Flutter",
    "dart/flutter": "Flutter",

    # REST API variants
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "restful api": "REST API",

    # CI/CD variants
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD",

    # Docker variants
    "docker": "Docker",
    "containerization": "Docker",
    "docker container": "Docker",

    # GraphQL variants
    "graphql": "GraphQL",
    "graph ql": "GraphQL",

    # React Native variants
    "react native": "React Native",
    "rn": "React Native",

    # Tailwind variants
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",

    # SQL variants
    "sql": "SQL",
    "mysql": "MySQL",
    "mssql": "SQL Server",
    "ms sql": "SQL Server",
    "sql server": "SQL Server",

    # Spark variants
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",

    # Generative AI & LLM aliases
    "generative ai": "Generative AI",
    "genai": "Generative AI",
    "gen ai": "Generative AI",
    "large language models": "Large Language Models",
    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "rag": "Retrieval-Augmented Generation",
    "retrieval-augmented generation": "Retrieval-Augmented Generation",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "langgraph": "LangGraph",
    "dspy": "DSPy",
    "vector databases": "Vector Databases",
    "chromadb": "ChromaDB",
    "pinecone": "Pinecone",
    "milvus": "Milvus",
    "qdrant": "Qdrant",
    "weaviate": "Weaviate",
    "mlops": "MLOps",

    # Modern AI Inference & Fine-Tuning aliases
    "vllm": "vLLM",
    "lora": "LoRA",
    "qlora": "QLoRA",
    "low-rank adaptation": "LoRA",
    "parameter efficient fine-tuning": "PEFT",
    "parameter-efficient fine-tuning": "PEFT",
    "flash attention": "FlashAttention",
    "flash_attention": "FlashAttention",
    "mistral ai": "Mistral",
    "anthropic claude": "Claude API",
    "claude": "Claude API",
    "google gemini": "Gemini API",
    "gemini": "Gemini API",
    "llama2": "LLaMA 2",
    "llama3": "LLaMA 3",
    "llama-2": "LLaMA 2",
    "llama-3": "LLaMA 3",
    "bits and bytes": "bitsandbytes",
    "guardrails": "Guardrails AI",
    "lite llm": "LiteLLM",

    # Data Engineering aliases
    "dbt": "dbt Core",
    "delta": "Delta Lake",
    "iceberg": "Apache Iceberg",
    "apache iceberg": "Apache Iceberg",
    "flink": "Apache Flink",
    "apache flink": "Apache Flink",
    "druid": "Apache Druid",
    "great expectations": "Great Expectations",
    "ge": "Great Expectations",

    # System design aliases
    "load balancer": "Load Balancing",
    "caching layer": "Caching",
    "message queue": "Message Queues",
    "mq": "Message Queues",
    "distributed system": "Distributed Systems",
    "ha": "High Availability",
    "event sourcing": "Event Sourcing",
    "service mesh": "Service Mesh",

    # Soft skill aliases
    "team lead": "Team Leadership",
    "tech lead": "Team Leadership",
    "technical lead": "Team Leadership",
    "mentoring": "Technical Mentoring",
    "code review": "Code Review",
    "pr review": "Code Review",
    "technical documentation": "Technical Writing",
    "tech writing": "Technical Writing",
    "cross functional": "Cross-functional Collaboration",
    "cross-functional": "Cross-functional Collaboration",

    # Core CS aliases
    "computer science": "Computer Science",
    "cs": "Computer Science",
    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "data analytics": "Data Analytics",
    "data analysis": "Data Analytics",
    "it integration": "IT Integration",
    "workflow orchestration": "Workflow Orchestration",
}

# Keys and values must EXACTLY match lowercased canonical names or known aliases.
IMPLIED_SKILLS: dict[str, list[str]] = {
    "machine learning": [
        "ml", "computer science", "artificial intelligence", "ai",
        "data analytics", "data analysis", "statistics",
    ],
    "deep learning": [
        "dl", "machine learning", "ml", "computer science",
        "artificial intelligence", "ai", "neural networks",
    ],
    "natural language processing": [
        "nlp", "natural language processing", "machine learning", "ml",
        "artificial intelligence", "ai", "computer science",
        "text mining",
    ],
    "nlp": [
        "natural language processing", "machine learning", "ml",
        "artificial intelligence", "ai", "computer science", "text mining",
    ],
    "retrieval-augmented generation": [
        "rag", "large language models", "llm", "llms",
        "generative ai", "genai", "artificial intelligence", "ai",
        "machine learning", "ml", "natural language processing", "nlp",
    ],
    "rag": [
        "retrieval-augmented generation", "large language models", "llm", "llms",
        "generative ai", "genai", "artificial intelligence", "ai",
        "machine learning", "ml",
    ],
    "langchain": [
        "large language models", "llm", "llms", "generative ai", "genai",
        "artificial intelligence", "ai", "workflow orchestration",
    ],
    "llamaindex": [
        "large language models", "llm", "llms", "generative ai", "genai",
        "artificial intelligence", "ai", "rag", "retrieval-augmented generation",
    ],
    "large language models": [
        "llm", "llms", "generative ai", "genai",
        "artificial intelligence", "ai",
        "nlp", "natural language processing", "machine learning", "ml",
    ],
    "llm": [
        "large language models", "llms", "generative ai", "genai",
        "artificial intelligence", "ai",
        "nlp", "natural language processing", "machine learning", "ml",
    ],
    "llms": [
        "large language models", "llm", "generative ai", "genai",
        "artificial intelligence", "ai",
        "nlp", "natural language processing", "machine learning", "ml",
    ],
    "generative ai": [
        "genai", "artificial intelligence", "ai",
        "machine learning", "ml",
    ],
    "genai": ["generative ai", "artificial intelligence", "ai", "machine learning", "ml"],
    "mlops": [
        "machine learning", "ml", "devops", "computer science",
        "model deployment", "workflow orchestration",
    ],
    "computer vision": [
        "machine learning", "ml", "artificial intelligence", "ai",
        "computer science", "deep learning", "dl",
    ],
    "reinforcement learning": [
        "machine learning", "ml", "artificial intelligence", "ai", "computer science",
    ],
    "data science": [
        "data analytics", "data analysis", "computer science",
        "statistics", "machine learning", "ml",
    ],
    "data analytics": ["data analysis", "statistics"],
    "data analysis": ["data analytics", "statistics"],
    # PyTorch/TF implies deep learning
    "pytorch": ["deep learning", "dl", "machine learning", "ml", "artificial intelligence", "ai"],
    "tensorflow": ["deep learning", "dl", "machine learning", "ml", "artificial intelligence", "ai"],
    "keras": ["deep learning", "dl", "machine learning", "ml"],
    # spaCy implies NLP
    "spacy": ["nlp", "natural language processing", "machine learning", "ml"],
    "nltk": ["nlp", "natural language processing", "machine learning", "ml"],
    "hugging face": [
        "nlp", "natural language processing", "large language models", "llm",
        "machine learning", "ml", "artificial intelligence", "ai",
    ],
    "transformers": [
        "nlp", "natural language processing", "large language models", "llm",
        "machine learning", "ml", "deep learning", "dl",
    ],
    "bert": ["nlp", "natural language processing", "large language models", "llm", "machine learning", "ml"],
    "gpt": ["nlp", "natural language processing", "large language models", "llm", "generative ai"],
    # Orchestration tools
    "airflow": ["workflow orchestration", "data pipeline", "it integration"],
    "prefect": ["workflow orchestration", "data pipeline", "it integration"],
    "dagster": ["workflow orchestration", "data pipeline", "it integration"],
    # Spark implies distributed computing & analytics
    "apache spark": ["data analytics", "data analysis", "big data"],
    "pyspark": ["apache spark", "data analytics", "data analysis", "python"],
}
