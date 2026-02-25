import express from "express";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";
import * as dotenv from "dotenv";
import db from "./server/db.js";

dotenv.config();

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Mock FAR Excerpts for RAG
  const FAR_CONTEXT = {
    part19: `
FAR 19.502-2 Total small business set-asides.
(a) Before setting aside an acquisition under this paragraph, the contracting officer shall first consider whether there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns (the "Rule of Two").
(b) The contracting officer shall set aside any acquisition over the micro-purchase threshold for small business participation when there is a reasonable expectation that offers will be obtained from at least two responsible small business concerns.
`,
    part22: `
FAR 22.403-1 Davis-Bacon Act.
The Davis-Bacon Act (40 U.S.C. 3141 et seq.) provides that contracts in excess of $2,000 to which the United States or the District of Columbia is a party for construction, alteration, or repair (including painting and decorating) of public buildings or public works within the United States, shall contain a clause that no laborer or mechanic employed directly upon the site of the work shall receive less than the prevailing wage rates as determined by the Secretary of Labor.
FAR 22.1002-1 General.
Service Contract Labor Standards (41 U.S.C. chapter 67) applies to contracts over $2,500 the principal purpose of which is to furnish services in the United States through the use of service employees.
`,
    part39: `
FAR 39.101 Policy.
(a) In acquiring information technology, agencies shall identify their requirements pursuant to OMB Circular A-130, including consideration of security of resources, protection of privacy, national security and emergency preparedness.
FAR 4.1902 Applicability.
This subpart applies to all acquisitions, including acquisitions of commercial products or commercial services, other than commercially available off-the-shelf items, when a contractor's information system may contain Federal contract information.
NIST SP 800-171 and CMMC requirements may apply depending on agency and data type (e.g., CUI).
`,
  };

  async function answerQueryWithRAG(
    question: string,
    mode: "part19" | "part22" | "part39",
  ) {
    const context = FAR_CONTEXT[mode];

    const prompt = `You are a US federal procurement compliance assistant.

Use ONLY the following FAR excerpts to answer the question.
Always:
- Cite specific sections as "FAR <section>".
- Explain your reasoning step by step.
- If you are not sure, say so and explain what additional info is needed.

FAR Excerpts:
${context}

Question: ${question}
`;

    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            answer: {
              type: Type.STRING,
              description: "The detailed reasoning and answer.",
            },
            citations: {
              type: Type.ARRAY,
              items: { type: Type.STRING },
              description: "List of citations like 'FAR 19.502-2'",
            },
            confidence: {
              type: Type.NUMBER,
              description: "Confidence score between 0 and 1.",
            },
            risk_level: {
              type: Type.STRING,
              description: "One of: 'low', 'medium', 'high'",
            },
          },
          required: ["answer", "citations", "confidence", "risk_level"],
        },
      },
    });

    const resultText = response.text;
    if (!resultText) {
      throw new Error("No response from Gemini");
    }

    const result = JSON.parse(resultText);

    return {
      answer: result.answer,
      citations: result.citations,
      confidence: result.confidence,
      risk_level: result.risk_level,
      citation_docs: [
        {
          section_id: `FAR ${mode.replace("part", "")}`,
          source_system: "FAR_MOCK",
          snippet: context.substring(0, 400) + "...",
        },
      ],
    };
  }

  app.get("/api/v1/health", (req, res) => {
    res.json({ status: "healthy", version: "0.1.0" });
  });

  app.post("/api/v1/compliance/set-aside-eligibility", async (req, res) => {
    try {
      const reqData = req.body;
      const q = `Determine if this acquisition should be set aside for small business under FAR Part 19. NAICS: ${reqData.naics}. Annual revenue: ${reqData.annual_revenue}. Employees: ${reqData.employee_count}. Contract value: ${reqData.contract_value}. Place of performance: ${reqData.place_of_performance}. Description: ${reqData.description}.`;

      const result = await answerQueryWithRAG(q, "part19");

      db.prepare(
        "INSERT INTO queries (workflow, query_params, response, confidence, risk_level) VALUES (?, ?, ?, ?, ?)",
      ).run(
        "part19",
        JSON.stringify(reqData),
        JSON.stringify(result),
        result.confidence,
        result.risk_level,
      );

      res.json({
        summary: result.answer.split("\n")[0].substring(0, 1000),
        risk_level: result.risk_level,
        confidence: result.confidence,
        reasoning: result.answer,
        citations: result.citations,
        citation_docs: result.citation_docs,
      });
    } catch (e: any) {
      res.status(500).json({ detail: e.message });
    }
  });

  app.post("/api/v1/compliance/labor-standards", async (req, res) => {
    try {
      const reqData = req.body;
      const q = `Determine which labor standards apply (Davis-Bacon, Service Contract Labor Standards, CWHSSA) under FAR Part 22. Contract type: ${reqData.contract_type}. Value: ${reqData.contract_value}. Location: ${reqData.location}. Description: ${reqData.description}.`;

      const result = await answerQueryWithRAG(q, "part22");

      db.prepare(
        "INSERT INTO queries (workflow, query_params, response, confidence, risk_level) VALUES (?, ?, ?, ?, ?)",
      ).run(
        "part22",
        JSON.stringify(reqData),
        JSON.stringify(result),
        result.confidence,
        result.risk_level,
      );

      res.json({
        summary: result.answer.split("\n")[0].substring(0, 1000),
        risk_level: result.risk_level,
        confidence: result.confidence,
        reasoning: result.answer,
        citations: result.citations,
        citation_docs: result.citation_docs,
      });
    } catch (e: any) {
      res.status(500).json({ detail: e.message });
    }
  });

  app.post("/api/v1/compliance/it-cyber", async (req, res) => {
    try {
      const reqData = req.body;
      const q = `Identify IT/cyber requirements and clauses under FAR Part 39 and related rules. Deployment: ${reqData.deployment}. Impact level: ${reqData.impact_level}. Data type: ${reqData.data_type}. Agency type: ${reqData.agency_type}. Description: ${reqData.description}.`;

      const result = await answerQueryWithRAG(q, "part39");

      db.prepare(
        "INSERT INTO queries (workflow, query_params, response, confidence, risk_level) VALUES (?, ?, ?, ?, ?)",
      ).run(
        "part39",
        JSON.stringify(reqData),
        JSON.stringify(result),
        result.confidence,
        result.risk_level,
      );

      res.json({
        summary: result.answer.split("\n")[0].substring(0, 1000),
        risk_level: result.risk_level,
        confidence: result.confidence,
        reasoning: result.answer,
        citations: result.citations,
        citation_docs: result.citation_docs,
      });
    } catch (e: any) {
      res.status(500).json({ detail: e.message });
    }
  });

  app.get("/api/v1/history", (req, res) => {
    try {
      const history = db
        .prepare("SELECT * FROM queries ORDER BY timestamp DESC LIMIT 50")
        .all();
      res.json(history);
    } catch (e: any) {
      res.status(500).json({ detail: e.message });
    }
  });

  app.post("/api/v1/chat", async (req, res) => {
    try {
      const { message } = req.body;
      const prompt = `You are a US federal procurement compliance assistant.
      
      User Message: ${message}
      
      Please provide a helpful, accurate response based on FAR regulations.
      `;

      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: prompt,
      });

      db.prepare(
        "INSERT INTO audit_logs (action, resource, metadata) VALUES (?, ?, ?)",
      ).run("CHAT_QUERY", "gemini", JSON.stringify({ message }));

      res.json({ response: response.text });
    } catch (e: any) {
      res.status(500).json({ detail: e.message });
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static("dist"));
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
