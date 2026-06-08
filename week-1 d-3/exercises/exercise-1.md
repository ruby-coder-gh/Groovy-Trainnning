# Exercise 1: 10 Bad Prompts → Good Prompts

> Rewrite 10 terrible prompts into something an AI can actually work with.

---

## 1. The Vague Feature Request

**❌ Bad:** *"Make a signup form."*

**✅ Good:**
```
Create a signup form in React with:
- Fields: full name, email, password, confirm password
- Client-side validation: email format, password min 8 chars, passwords match
- Show inline error messages below each field
- Submit button that logs form data to console
- Style with Tailwind CSS, centered layout, white card on gray bg
```

---

## 2. The Context-Free Debug

**❌ Bad:** *"It doesn't work. Fix it."*

**✅ Good:**
```
I'm getting this error when I run my Express server:
"TypeError: Cannot read properties of undefined (reading 'id')"

Code (server.js lines 24-30):
app.put('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === req.body.id);
  res.json(user);
});

I expected it to find the user by URL param (req.params.id), not body.
Fix the code and explain what was wrong.
```

---

## 3. The Kitchen Sink

**❌ Bad:** *"Build a full social media app with posts, comments, likes, followers, DMs, notifications, stories, reels, and a dark mode toggle."*

**✅ Good:**
```
We're building a social media app step by step.

Step 1: Create the database schema for:
- Users (id, username, email, password_hash, created_at)
- Posts (id, user_id FK, content, image_url, created_at)
- Comments (id, post_id FK, user_id FK, content, created_at)

Use PostgreSQL syntax. Add indexes on foreign keys.

Only answer Step 1. I'll ask for more steps after.
```

---

## 4. The Zero-Context Code Gen

**❌ Bad:** *"Write a function to sort data."*

**✅ Good:**
```
Write a JavaScript function that sorts an array of objects by a given key.

Requirements:
- Function signature: sortByKey(array, key, order = 'asc')
- order can be 'asc' or 'desc'
- Should NOT mutate the original array
- Handle edge cases: empty array, missing key, non-array input
- Use pure JS, no lodash

Example usage:
sortByKey([{name: 'John', age: 30}, {name: 'Alice', age: 25}], 'age', 'asc')
// Returns [{name: 'Alice', age: 25}, {name: 'John', age: 30}]
```

---

## 5. The Assume-I-Know-Everything

**❌ Bad:** *"Add auth middleware."*

**✅ Good:**
```
Add JWT authentication middleware to an Express.js app (Node 18+).

Requirements:
- Middleware function: authenticate(req, res, next)
- Reads token from Authorization header (Bearer scheme)
- Verifies using jsonwebtoken library with secret from process.env.JWT_SECRET
- On success: attach decoded user to req.user and call next()
- On failure: return 401 with { error: 'Invalid or expired token' }
- Export as module

Show the code and a brief usage example in app.js.
```

---

## 6. The No-Output-Format

**❌ Bad:** *"Tell me about REST API conventions."*

**✅ Good:**
```
Explain REST API conventions for these aspects.
Format your response as a table with: Aspect | Convention | Example

Cover:
1. URL structure (plural nouns)
2. HTTP methods (GET, POST, PUT, DELETE)
3. Status codes (200, 201, 204, 400, 404, 500)
4. Request/response format (JSON)
5. Error response format
```

---

## 7. The Make-It-Pretty

**❌ Bad:** *"Make it look better."*

**✅ Good:**
```
Improve the CSS of this React component. Current issues:
- No padding around the container
- Default system font
- Flat colors, no shadows
- Buttons have no hover states

Apply these changes:
- Container: max-width 600px, margin auto, padding 24px
- Font: 'Inter' from Google Fonts (fallback: system-ui)
- Background: white (#ffffff) with border-radius 12px and box-shadow
- Buttons: padding 10px 20px, bg #3b82f6, white text, rounded 8px
- Hover: buttons darken to #2563eb, cards lift with larger shadow
```

---

## 8. The Too-Many-Assumptions

**❌ Bad:** *"Deploy my app."*

**✅ Good:**
```
I want to deploy a Node.js + React app. Help me choose a deployment strategy.

Context:
- Backend: Express.js with PostgreSQL (hosted on Render)
- Frontend: Vite + React (static build)
- Git repo: GitHub
- Budget: free tier preferred

Give me two options with pros/cons:
1. Render (backend + frontend together)
2. Vercel (frontend) + Render (backend)
```

---

## 9. The No-Example Request

**❌ Bad:** *"Create a function that transforms data."*

**✅ Good:**
```
Write a TypeScript function that transforms an array of user objects.

Input format:
[{ id: 1, firstName: 'John', lastName: 'Doe', email: 'john@example.com' }]

Desired output format:
[{ id: 1, fullName: 'John Doe', email: 'john@example.com' }]

Requirements:
- Combine firstName and lastName into fullName
- Keep id and email unchanged
- Handle empty arrays
- TypeScript with proper interfaces
- Pure function, no side effects
```

---

## 10. The Single-Response Trap

**❌ Bad:** *"Explain everything about databases."*

**✅ Good:**
```
Explain database indexing for a beginner backend developer.

Cover:
1. What is an index? (simple analogy)
2. How indexes work under the hood (B-tree briefly)
3. When to use indexes (WHERE, JOIN, ORDER BY)
4. When NOT to use indexes (small tables, frequent writes)
5. A simple SQL example: CREATE INDEX idx_users_email ON users(email);

Keep it to 3 short paragraphs. No fluff.
```

---

## Key Takeaways 🎯

| Mistake | Fix |
|---------|-----|
| Too vague | Add specific requirements |
| No context | Explain the situation |
| Everything at once | Break into steps |
| No format | Specify output structure |
| No examples | Show input/output |
| Assumptions | State your stack explicitly |
