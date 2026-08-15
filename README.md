# Umoja Terra - Hono JavaScript Backend

Ultra-fast, zero cold-start JavaScript backend powered by **Hono**.

Designed to run either:
1. **At the Edge on Cloudflare Workers** with Serverless SQL (Cloudflare D1) — `<5ms` cold start worldwide.
2. **On Node.js / Render** with local persistent storage — ready for traditional cloud deployments.

---

## 📁 Project Structure

* **`src/index.js`**: Complete Hono API application containing all 20+ REST endpoints (Auth, Countries, Plots, Inquiries, Admin Approvals, Suspension, Visibility, and 7-day Analytics).
* **`src/db.js`**: Universal database adapter supporting both Cloudflare D1 serverless bindings and Node.js storage.
* **`src/serializers.js`**: Data formatters and African flag lookup tables.
* **`src/seed.js`**: Database initialization script that seeds the clean slate default admin account (`admin` / `admin`).
* **`src/server-node.js`**: Local Node.js server runner (`http://localhost:8000`).
* **`schema.sql`**: SQL schema definitions for Cloudflare D1 and SQLite.
* **`wrangler.toml`**: Cloudflare Workers deployment configuration.

---

## 🚀 Running Locally

```bash
# 1. Install dependencies
npm install

# 2. Seed initial admin account
npm run seed

# 3. Start development server
npm run dev
```

The server will be live on `http://localhost:8000`.

---

## ☁️ Deploying to Cloudflare Workers (Edge)

```bash
# 1. Login to Cloudflare
npx wrangler login

# 2. Create your D1 Database
npx wrangler d1 create umoja_db

# 3. Apply the SQL schema to D1
npx wrangler d1 execute umoja_db --file=schema.sql

# 4. Deploy your API globally
npm run deploy
```
