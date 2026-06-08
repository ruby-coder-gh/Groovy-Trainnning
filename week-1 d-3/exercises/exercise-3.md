# Exercise 3: Few-Shot Prompting

> Give 3 examples → AI infers the pattern → applies to new input.  
> No explicit instructions needed — the examples DO the teaching.

---

## Example 1: SQL Query Generator

**Task:** Convert natural language to SQL queries.

### Shots (Examples)

**Input:** "Find all users who signed up in the last 7 days."
**Output:**
```sql
SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days';
```

**Input:** "Count how many orders were placed yesterday."
**Output:**
```sql
SELECT COUNT(*) as order_count FROM orders WHERE DATE(created_at) = CURRENT_DATE - 1;
```

**Input:** "Show me the top 5 most expensive products that are in stock."
**Output:**
```sql
SELECT * FROM products WHERE stock > 0 ORDER BY price DESC LIMIT 5;
```

### New Input (No Instruction Given)

**Input:** "Get all customers who have spent more than $500 total."
**Output (AI followed the pattern):**
```sql
SELECT c.*, SUM(o.total) as total_spent
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id
HAVING total_spent > 500;
```

✅ **Pattern learned:** Natural language → SQL, using `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `JOIN`, `GROUP BY` as needed. No prompting about SQL syntax required.

---

## Example 2: Code Comment Generator

**Task:** Add meaningful comments to code snippets.

### Shots (Examples)

**Input:**
```js
const users = await db.query('SELECT * FROM users WHERE active = true');
```
**Output:**
```js
// Fetch all active users from the database
const users = await db.query('SELECT * FROM users WHERE active = true');
```

**Input:**
```js
const total = cart.items.reduce((sum, item) => sum + item.price * item.qty, 0);
```
**Output:**
```js
// Calculate the total cost of all items in the cart (price × quantity)
const total = cart.items.reduce((sum, item) => sum + item.price * item.qty, 0);
```

**Input:**
```js
const token = jwt.sign({ userId: user.id, role: user.role }, SECRET, { expiresIn: '24h' });
```
**Output:**
```js
// Generate a JWT with user ID and role, valid for 24 hours
const token = jwt.sign({ userId: user.id, role: user.role }, SECRET, { expiresIn: '24h' });
```

### New Input (No Instruction Given)

**Input:**
```js
const sorted = data.sort((a, b) => new Date(b.date) - new Date(a.date));
```
**Output (AI followed the pattern):**
```js
// Sort data by date in descending order (newest first)
const sorted = data.sort((a, b) => new Date(b.date) - new Date(a.date));
```

✅ **Pattern learned:** Single-line comment before code, explaining WHAT and WHY (not just what). Consistent tone.

---

## Example 3: Error Message Translator

**Task:** Turn technical error messages into human-friendly explanations + fix suggestions.

### Shots (Examples)

**Input:** `Error: ENOENT: no such file or directory, open './config.json'`
**Output:**
```
😕 The app tried to open a file called 'config.json' but it doesn't exist.

Fix: Check that config.json is in the right folder. 
If it's missing, create one using: cp config.example.json config.json
```

**Input:** `TypeError: Cannot read properties of null (reading 'length')`
**Output:**
```
😕 You're trying to get the .length of something that is null (empty/nothing).

Fix: Add a check before accessing length:
  if (myVariable && myVariable.length > 0) { ... }
Make sure the variable is initialized before using it.
```

**Input:** `Error: listen EADDRINUSE :::3000`
**Output:**
```
😕 Port 3000 is already being used by another process.

Fix: Either:
  1. Kill the process: lsof -ti:3000 | xargs kill -9
  2. Use a different port: change PORT=3001 in your .env
```

### New Input (No Instruction Given)

**Input:** `MongoError: E11000 duplicate key error collection: users index: email_1 dup key: { email: "test@test.com" }`
**Output (AI followed the pattern):**
```
😕 A user with the email 'test@test.com' already exists in the database.

Fix: Use a unique email address, or add an update option:
  - Try: db.collection.updateOne({email: email}, {$set: data}, {upsert: true})
  - Check if you meant to update an existing record instead of creating a new one
```

✅ **Pattern learned:** Emoji + plain English explanation → specific fix suggestion(s). Tone is helpful, not robotic.

---

## What I Learned 🧠

| Aspect | Observation |
|--------|------------|
| **Number of shots** | 3 is the sweet spot. 1-2 can be ambiguous, 3 locks in the pattern |
| **Pattern variety** | Each example should show a DIFFERENT case of the same rule |
| **No instructions needed** | If examples are clear, you don't need to explain the rule |
| **Edge case handling** | Include 1 edge case in your 3 shots to teach error handling |
| **Consistency** | The output style matches the examples almost exactly |

> *"Few-shot prompting is like teaching a kid by showing, not telling. Three good examples beat ten instructions."*
