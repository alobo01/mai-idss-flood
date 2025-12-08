import { Router } from 'express';

const router = Router();

/**
 * @swagger
 * /health:
 *   get:
 *     tags: [Health]
 *     summary: Health check endpoint
 *     description: Check the health status of the API and database connection
 *     responses:
 *       200:
 *         description: Service is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: healthy
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 uptime:
 *                   type: number
 *                   description: Service uptime in seconds
 *                 database:
 *                   type: object
 *                   properties:
 *                     status:
 *                       type: string
 *                       enum: [connected, disconnected]
 *                     latency:
 *                       type: number
 *                       description: Database query latency in milliseconds
 *       503:
 *         description: Service is unhealthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: unhealthy
 *                 error:
 *                   type: string
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 */
router.get('/', async (req, res) => {
  const start = Date.now();
  let dbStatus = 'disconnected';
  let dbLatency = null;

  try {
    await req.pool.query('SELECT 1');
    dbStatus = 'connected';
    dbLatency = Date.now() - start;
  } catch (error) {
    console.error('Database health check failed:', error);
    return res.status(503).json({
      status: 'unhealthy',
      error: 'Database connection failed',
      timestamp: new Date().toISOString(),
      database: {
        status: dbStatus,
        error: error.message
      }
    });
  }

  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    database: {
      status: dbStatus,
      latency: dbLatency
    }
  });
});

export default router;