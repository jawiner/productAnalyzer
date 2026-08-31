// Concurrency test for the double-booking guard (migration 0001's
// appointments_no_overlap_* exclusion constraints).
//
// Verified against a real Postgres 16 instance: 10 concurrent INSERTs at
// the identical (employee_id, time range) resulted in exactly 1 success and
// 9 rejections with error code 23P01 (exclusion_violation); the same was
// separately confirmed for the no-employee/per-service constraint. Not
// wired into CI — requires a live Postgres with the schema from
// supabase/migrations applied (a local `supabase start` stack, or a
// scratch Supabase project / Docker container).
//
// Usage:
//   DATABASE_URL=postgres://postgres:postgres@localhost:54322/postgres \
//     node supabase/tests/concurrent_booking.test.js
//
// What it proves: firing N concurrent INSERTs at the exact same
// (employee_id, time range) results in exactly 1 success and N-1 failures
// with Postgres error code 23P01 (exclusion_violation) — i.e. the database
// itself is the source of truth for no-double-booking, not application code
// racing a SELECT-then-INSERT.

const { Client } = require('pg'); // npm i pg (devDependency) before running

const DATABASE_URL = process.env.DATABASE_URL;
const CONCURRENT_REQUESTS = 10;

async function withClient(fn) {
  const client = new Client({ connectionString: DATABASE_URL });
  await client.connect();
  try {
    return await fn(client);
  } finally {
    await client.end();
  }
}

async function setupFixture() {
  return withClient(async (client) => {
    const business = await client.query(
      `insert into businesses (slug, name) values ('concurrency-test', 'Concurrency Test') returning id`
    );
    const businessId = business.rows[0].id;

    await client.query(`insert into business_settings (business_id) values ($1)`, [businessId]);

    const service = await client.query(
      `insert into services (business_id, name, duration_minutes) values ($1, 'Test Service', 30) returning id`,
      [businessId]
    );
    const serviceId = service.rows[0].id;

    const employee = await client.query(
      `insert into employees (business_id, name) values ($1, 'Test Employee') returning id`,
      [businessId]
    );
    const employeeId = employee.rows[0].id;

    const customer = await client.query(
      `insert into customers (business_id, full_name, phone) values ($1, 'Load Test Customer', '0500000000') returning id`,
      [businessId]
    );
    const customerId = customer.rows[0].id;

    return { businessId, serviceId, employeeId, customerId };
  });
}

async function attemptBooking({ businessId, serviceId, employeeId, customerId }, startsAt, endsAt) {
  return withClient(async (client) => {
    try {
      await client.query(
        `insert into appointments (business_id, service_id, employee_id, customer_id, starts_at, ends_at)
         values ($1, $2, $3, $4, $5, $6)`,
        [businessId, serviceId, employeeId, customerId, startsAt, endsAt]
      );
      return { ok: true };
    } catch (err) {
      return { ok: false, code: err.code, message: err.message };
    }
  });
}

async function cleanup(businessId) {
  await withClient((client) => client.query(`delete from businesses where id = $1`, [businessId]));
}

async function main() {
  if (!DATABASE_URL) {
    console.error('Set DATABASE_URL to a Postgres instance with the migrations applied.');
    process.exit(1);
  }

  const fixture = await setupFixture();
  const startsAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
  const endsAt = new Date(Date.now() + 24 * 60 * 60 * 1000 + 30 * 60 * 1000).toISOString();

  try {
    const results = await Promise.all(
      Array.from({ length: CONCURRENT_REQUESTS }, () => attemptBooking(fixture, startsAt, endsAt))
    );

    const successes = results.filter((r) => r.ok);
    const conflicts = results.filter((r) => !r.ok && r.code === '23P01');
    const otherErrors = results.filter((r) => !r.ok && r.code !== '23P01');

    console.log(`Concurrent booking attempts: ${CONCURRENT_REQUESTS}`);
    console.log(`  Succeeded: ${successes.length}`);
    console.log(`  Rejected as overlap (23P01): ${conflicts.length}`);
    console.log(`  Other errors: ${otherErrors.length}`);
    if (otherErrors.length > 0) console.log(otherErrors);

    if (successes.length === 1 && conflicts.length === CONCURRENT_REQUESTS - 1 && otherErrors.length === 0) {
      console.log('PASS: exactly one booking succeeded, all others correctly rejected.');
      process.exitCode = 0;
    } else {
      console.error('FAIL: double-booking guard did not behave as expected.');
      process.exitCode = 1;
    }
  } finally {
    await cleanup(fixture.businessId);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
