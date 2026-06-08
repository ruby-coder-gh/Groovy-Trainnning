# Exercise 2: Same Task — 5 Different Prompt Styles

> **Task:** Generate a Todo API endpoint (GET /api/todos)  
> **Style:** 5 different approaches — compare the outputs.

---

## Style 1: Direct & Minimal

**Prompt:**
```
Write an Express.js route for GET /api/todos. Return a JSON array of todo objects.
Each todo has: id, title, completed (boolean), created_at.
Use an in-memory array with 3 hardcoded sample todos.
```

**Output Quality:** ⚡ Fast, clean, but basic. No error handling, no comments. Gets the job done but feels like a skeleton.

**Verdict:** Good for quick scaffolding when you know what you want.

---

## Style 2: Role-Based

**Prompt:**
```
You are a senior backend engineer at a fast-growing startup. 
You follow REST conventions, write clean modular code, and always add error handling.

Write a GET /api/todos route for an Express.js app.
- Use an in-memory array as data source
- Return proper status codes
- Add try/catch error handling
- Include JSDoc comments
- Make it production-ready
```

**Output Quality:** 🏆 Much better. Added error handling, JSDoc, proper HTTP status codes (200 vs 304), and a consistent code style.

**Verdict:** Role-based prompts unlock the AI's "best behavior." Highly recommended.

---

## Style 3: Chain-of-Thought (Step-by-Step)

**Prompt:**
```
I need to build a GET /api/todos endpoint. Let's think through this step by step.

Step 1: What data structure should I use for todos?
Step 2: Where should the data be stored?
Step 3: How do I handle the GET request?
Step 4: What edge cases should I consider?
Step 5: Write the final code.

Walk me through each step before writing the final solution.
```

**Output Quality:** 🤔 Detailed reasoning but took longer. The AI explained WHY it made each decision (in-memory vs DB, array vs Map, etc.). Great for **learning** but slower for **shipping**.

**Verdict:** Best for complex problems or when you're learning a new concept. Overkill for simple CRUD.

---

## Style 4: Constraint-Heavy

**Prompt:**
```
Write a GET /api/todos route. CONSTRAINTS:
- NO external packages (only express)
- NO database, use a simple array
- NO arrow functions (use function keyword)
- MAX 20 lines of code
- MUST include a comment on line 1
- MUST return HTTP 200 with JSON array
- Data source must be named 'todoList'
```

**Output Quality:** 🎯 Very precise. Hit all constraints perfectly but felt rigid. The AI prioritized meeting constraints over code quality — variable names were terse, no error handling.

**Verdict:** Useful when you have strict coding standards or size limits. Otherwise, too restrictive.

---

## Style 5: Example-Driven

**Prompt:**
```
Write a GET /api/todos route following this exact pattern:

EXAMPLE ROUTE (GET /api/users):
app.get('/api/users', (req, res) => {
  try {
    res.status(200).json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

DATA MODEL:
User = { id, name, email }
Todo = { id, title, completed, created_at }

Now write GET /api/todos following the SAME pattern:
- Same error handling style
- Same JSON response format
- Same HTTP status codes
- With 3 sample todos pre-loaded
```

**Output Quality:** 🏆🏆 **Perfect.** The AI matched the style exactly — same error handling, same response format, same code patterns. It even used the same comment style from the example.

**Verdict:** Most reliable for consistent output. Show once, get matching code forever.

---

## Comparison Table

| Style | Quality | Speed | Best For |
|-------|---------|-------|----------|
| Direct & Minimal | ⚡⚡ | 🚀 | Quick scaffolds |
| Role-Based | ⚡⚡⚡⚡ | 🚀🚀 | Production code |
| Chain-of-Thought | ⚡⚡⚡ | 🐢 | Learning complex topics |
| Constraint-Heavy | ⚡⚡⚡ | 🚀 | Strict requirements |
| **Example-Driven** 🏆 | **⚡⚡⚡⚡⚡** | **🚀🚀** | **Consistent quality** |

---

## My Pick 🏆

**Example-Driven** + **Role-Based** combo:

> *"You are a senior backend engineer. Write a GET /api/todos route following this exact pattern: [example]. Match the style, error handling, and conventions exactly."*

Gives you the quality of role-based with the consistency of example-driven. Best of both worlds.
