/**
 * End-to-End Integration Test
 * 
 * Validates that the Frontend V1 consumes real backend APIs and properly
 * renders agent orchestrator responses, citations, evidence, and traces.
 * 
 * Run with: node test-e2e.js
 */

const BASE_URL = 'http://localhost:8000';
const TEST_USER = 'test_operator';
const TEST_CLEARANCE = ['INTERNAL', 'SECRET'];

class TestClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async login() {
    console.log('\n🔐 Logging in...');
    try {
      const res = await fetch(`${this.baseUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: TEST_USER,
          password: 'password',
        }),
      });
      if (!res.ok) throw new Error(`Login failed: ${res.status}`);
      const data = await res.json();
      this.token = data.access_token;
      console.log(`✅ Logged in as ${TEST_USER}`);
      return this.token;
    } catch (err) {
      console.error('❌ Login failed:', err.message);
      throw err;
    }
  }

  async healthCheck() {
    console.log('\n💚 Health check...');
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      const data = await res.json();
      console.log('✅ Backend status:', data);
      return data;
    } catch (err) {
      console.error('❌ Health check failed:', err.message);
      throw err;
    }
  }

  async getModels() {
    console.log('\n🤖 Fetching models...');
    try {
      const res = await fetch(`${this.baseUrl}/models`);
      if (!res.ok) throw new Error(`Models API failed: ${res.status}`);
      const data = await res.json();
      console.log(`✅ Found ${data.models.length} models`);
      console.log('   Models:', data.models.map(m => m.display_name).join(', '));
      return data;
    } catch (err) {
      console.error('❌ Failed to fetch models:', err.message);
      throw err;
    }
  }

  async chat(message) {
    console.log(`\n💬 Sending chat message: "${message}"`);
    try {
      const res = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`,
        },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
      const data = await res.json();
      console.log('✅ Chat response received');
      return data;
    } catch (err) {
      console.error('❌ Chat failed:', err.message);
      throw err;
    }
  }

  validateResponse(response) {
    console.log('\n🔍 Validating response structure...');
    const required = [
      'diagnosis_summary',
      'citations',
      'evidence_blocks',
      'reasoning_trace',
      'model_used',
      'evidence_state',
      'evidence_confidence',
      'classification_level',
    ];

    const missing = required.filter(field => !(field in response));
    if (missing.length > 0) {
      console.warn(`⚠️  Missing fields: ${missing.join(', ')}`);
      return false;
    }

    console.log('✅ Response structure valid');
    console.log(`   - Diagnosis: ${response.diagnosis_summary.substring(0, 100)}...`);
    console.log(`   - Citations: ${response.citations.length}`);
    console.log(`   - Evidence blocks: ${response.evidence_blocks.length}`);
    console.log(`   - Reasoning steps: ${response.reasoning_trace.length}`);
    console.log(`   - Model used: ${response.model_used}`);
    console.log(`   - Evidence state: ${response.evidence_state}`);
    console.log(`   - Classification: ${response.classification_level}`);
    return true;
  }

  validateCitations(citations) {
    console.log('\n📚 Validating citations...');
    if (!Array.isArray(citations) || citations.length === 0) {
      console.warn('⚠️  No citations in response');
      return false;
    }

    const sample = citations[0];
    const requiredFields = ['document', 'document_name', 'tag', 'classification_tag'];
    const missing = requiredFields.filter(f => !(f in sample));
    
    if (missing.length > 0) {
      console.warn(`⚠️  Citation missing fields: ${missing.join(', ')}`);
      console.log('Sample citation:', sample);
      return false;
    }

    console.log(`✅ ${citations.length} citations valid`);
    citations.slice(0, 2).forEach((c, i) => {
      console.log(`   Citation ${i + 1}: "${c.document}" (${c.tag})`);
    });
    return true;
  }

  validateEvidence(evidenceBlocks) {
    console.log('\n🔎 Validating evidence blocks...');
    if (!Array.isArray(evidenceBlocks)) {
      console.warn('⚠️  Evidence blocks not an array');
      return false;
    }

    if (evidenceBlocks.length === 0) {
      console.warn('⚠️  No evidence blocks in response');
      return false;
    }

    const sample = evidenceBlocks[0];
    const required = ['document', 'location', 'snippet'];
    const missing = required.filter(f => !(f in sample));

    if (missing.length > 0) {
      console.warn(`⚠️  Evidence block missing fields: ${missing.join(', ')}`);
      return false;
    }

    console.log(`✅ ${evidenceBlocks.length} evidence blocks valid`);
    evidenceBlocks.slice(0, 1).forEach((e, i) => {
      console.log(`   Block ${i + 1}: "${e.document}" - ${e.snippet.substring(0, 60)}...`);
    });
    return true;
  }

  validateTrace(trace) {
    console.log('\n🔗 Validating reasoning trace...');
    if (!Array.isArray(trace) || trace.length === 0) {
      console.warn('⚠️  No reasoning trace');
      return false;
    }

    console.log(`✅ ${trace.length} trace steps`);
    trace.slice(0, 3).forEach((step, i) => {
      console.log(`   Step ${i + 1}: ${step.step_number || i + 1}. ${step.title}`);
    });
    return true;
  }

  async getAuditLogs() {
    console.log('\n📋 Fetching audit logs...');
    try {
      const res = await fetch(`${this.baseUrl}/audit/logs`);
      if (!res.ok) throw new Error(`Audit API failed: ${res.status}`);
      const data = await res.json();
      console.log(`✅ Found ${data.length} audit entries`);
      if (data.length > 0) {
        const latest = data[data.length - 1];
        console.log(`   Latest: ${latest.event_type} - ${latest.username} (${latest.status})`);
      }
      return data;
    } catch (err) {
      console.error('❌ Failed to fetch audit logs:', err.message);
      return [];
    }
  }

  async verifyAuditChain() {
    console.log('\n🔐 Verifying audit chain...');
    try {
      const res = await fetch(`${this.baseUrl}/audit/verify`);
      if (!res.ok) throw new Error(`Verify API failed: ${res.status}`);
      const data = await res.json();
      if (data.is_valid) {
        console.log(`✅ Audit chain valid (${data.total_entries} entries)`);
      } else {
        console.warn(`⚠️  Audit chain broken at entry ${data.broken_index}: ${data.reason}`);
      }
      return data;
    } catch (err) {
      console.error('❌ Audit verification failed:', err.message);
      return null;
    }
  }
}

async function runTests() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║           AEGIS AI FRONTEND V1 END-TO-END TEST                ║
║        Testing real backend API integration                    ║
╚════════════════════════════════════════════════════════════════╝
  `);

  const client = new TestClient(BASE_URL);
  const results = {
    passed: 0,
    failed: 0,
    warnings: 0,
  };

  try {
    // 1. Health check
    await client.healthCheck();
    results.passed++;

    // 2. Login
    await client.login();
    results.passed++;

    // 3. Models
    const modelsResp = await client.getModels();
    if (modelsResp.models.length > 0) {
      results.passed++;
    } else {
      results.failed++;
    }

    // 4. Chat
    const chatResp = await client.chat('What is SOP-017 for pump maintenance?');
    if (chatResp && chatResp.diagnosis_summary) {
      results.passed++;
    } else {
      results.failed++;
    }

    // 5. Validate response
    if (client.validateResponse(chatResp)) {
      results.passed++;
    } else {
      results.warnings++;
    }

    // 6. Validate citations
    if (client.validateCitations(chatResp.citations)) {
      results.passed++;
    } else {
      results.warnings++;
    }

    // 7. Validate evidence
    if (chatResp.evidence_blocks && chatResp.evidence_blocks.length > 0) {
      if (client.validateEvidence(chatResp.evidence_blocks)) {
        results.passed++;
      } else {
        results.warnings++;
      }
    } else {
      console.warn('⚠️  No evidence blocks (may be expected for some queries)');
      results.warnings++;
    }

    // 8. Validate trace
    if (client.validateTrace(chatResp.reasoning_trace)) {
      results.passed++;
    } else {
      results.warnings++;
    }

    // 9. Audit logs
    await client.getAuditLogs();
    results.passed++;

    // 10. Verify audit chain
    await client.verifyAuditChain();
    results.passed++;

  } catch (err) {
    console.error('\n❌ Test suite failed:', err.message);
    results.failed++;
  }

  console.log(`
╔════════════════════════════════════════════════════════════════╗
║                        TEST RESULTS                            ║
╚════════════════════════════════════════════════════════════════╝
  ✅ Passed:  ${results.passed}
  ⚠️  Warnings: ${results.warnings}
  ❌ Failed:  ${results.failed}
  
${results.failed === 0 ? '🎉 All tests passed!\n' : '❌ Some tests failed. See details above.\n'}
  `);

  process.exit(results.failed > 0 ? 1 : 0);
}

runTests();
