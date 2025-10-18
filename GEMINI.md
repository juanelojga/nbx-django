# Gemini

This project is a Django-based application for package handling.

### 1. 🎯 Project Architecture & Guiding Principles

This is a **Django/Graphene (GraphQL) API** project using **PostgreSQL** for persistence.

* **Primary Database:** PostgreSQL (Django ORM is the interface).
* **API Interface:** GraphQL, powered by **Graphene-Django**.
* **Core Constraint:** All data interaction (reads, writes, updates) must be exposed exclusively through the **GraphQL Schema**. Do not generate or suggest REST API views.
* **Performance Focus:** Always prioritize efficient database interaction.

---

### 2. 📁 Structure and Naming Conventions

* **Schema Files:** The root GraphQL schema is in `core/schema.py`. App-specific types, queries, and mutations are in `posts/schema.py`.

| Component | Convention | Example |
| :--- | :--- | :--- |
| **Django Model** | Singular, PascalCase | `Post`, `Author` |
| **GraphQL Type** | Uses `Type` suffix | `PostType`, `AuthorType` |
| **Query Resolver** | Uses `resolve_` prefix | `resolve_all_posts` |
| **Mutation Class**| Uses action verb prefix | `CreatePost`, `DeleteComment` |

---

### 3. 📝 Coding and Graphene Best Practices

1.  **Code Style:** Adhere strictly to **PEP 8** standards.
2.  **Database Efficiency:** When writing **Graphene resolvers**, you **must** use **`select_related()`** or **`prefetch_related()`** to prevent the N+1 problem.
3.  **Data Writes:** All data modification logic must be implemented within a **Graphene Mutation class**. Never place write logic in a Query resolver.

---

### 4. ✅ Workflow and Tooling Instructions

1.  **Testing Framework:** Use **`pytest`** and **`pytest-django`** for generating tests.
2.  **Test Location:** Place all generated tests in the **`nbxdjango/packagehandling/tests/`** directory.
3.  **Code Quality & Formatting Commands (CRITICAL):**
    When generating or modifying code, ensure it adheres to the following tools:
    * **Check style issues:** `flake8 .`
    * **Auto-format code:** `black .`
    * **Organize imports:** `isort .`
    * **Type checking:** `mypy .`
4.  **Test Execution Command (CRITICAL):**
    The full command required to run tests and verify code changes is:

    ```bash
    DJANGO_SETTINGS_MODULE=nbxdjango.settings DATABASE_URL=postgres://myuser:mypassword@localhost:5432/mydatabase pytest nbxdjango/packagehandling/tests/
    ```

    **When asked to run tests or verify code,** you must use this **entire command string**. Substitute the specific test file path (e.g., `.../tests/test_models.py`) if the request is for a subset of tests.

5.  **Test Generation:** When creating a new test, include the necessary model fixture creation and the full GraphQL query/mutation needed to execute the logic against the PostgreSQL database.
