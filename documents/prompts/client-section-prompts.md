# Prompt: Update CreateClient Mutation

You are working in a **Django PostgreSQL Graphene project** that serves as the backend for an application focused on **package handling** with entities such as users, clients, packages, and consolidates.

## Context

- There are **two user types**: `admin` and `client`.
- Only **admin users** can manage clients.
- Each `client` is associated with a user of type `client`.

The target file is `client_mutations.py`.

Currently, the `CreateClient` mutation defines multiple required arguments, including `password`.

## Task

Modify the `CreateClient` mutation according to the following requirements:

1. **Required fields:** Only `first_name`, `last_name`, and `email` must remain required.
2. **Optional fields:** All other parameters (`identification_number`, `state`, `city`, `main_street`, `secondary_street`, `building_number`, `mobile_phone_number`, `phone_number`) should be **optional**.
3. **Password handling:**
   - Do **not** request `password` as a mutation argument.
   - Generate a **secure random password** when creating the user.
   - Use a method such as `secrets.token_urlsafe(16)` or Django’s built-in password generator to ensure it’s hard to hack.
4. **Permissions:** Keep the same permission logic — only **superusers** can create clients.
5. **Keep the mutation structure and return value the same.**
6. **Do not add or modify any unit test cases, and do not create or run any test cases.**

## Additional Instructions

- Ensure the mutation follows the same coding style and conventions already used in the project.
- Do not change any other mutations.
- After updating, recheck that the mutation still returns `CreateClient(client=client)` as before.

## Output

Return only the updated code of the `CreateClient` mutation class with the described modifications — no explanations or comments.