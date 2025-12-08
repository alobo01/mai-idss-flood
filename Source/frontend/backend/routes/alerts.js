import { Router } from 'express';
import { alertStatus, alertSeverityDisplay } from '../utils/helpers.js';

const router = Router();

/**
 * @swagger
 * /api/alerts:
 *   get:
 *     tags: [Alerts]
 *     summary: Get alerts with filtering
 *     description: Retrieve alerts with optional severity filtering
 *     parameters:
 *       - in: query
 *         name: severity
 *         schema:
 *           type: string
 *           enum: [low, medium, high, critical]
 *         description: Alert severity filter
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 50
 *         description: Maximum number of alerts to return
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                   zoneId:
 *                     type: string
 *                   severity:
 *                     type: string
 *                   type:
 *                     type: string
 *                   title:
 *                     type: string
 *                   description:
 *                     type: string
 *                   status:
 *                     type: string
 *                   timestamp:
 *                     type: string
 *                     format: date-time
 */
router.get('/', async (req, res) => {
  try {
    const { severity, limit = 50 } = req.query;

    let query = `
      SELECT
        a.*,
        z.name as zone_name,
        z.code as zone_code
      FROM alerts a
      JOIN zones z ON a.zone_id = z.id
      WHERE a.created_at >= NOW() - INTERVAL '72 hours'
    `;

    const params = [];
    let paramIndex = 1;

    if (severity) {
      query += ` AND a.severity = $${paramIndex++}`;
      params.push(severity);
    }

    query += ` ORDER BY a.created_at DESC LIMIT $${paramIndex++}`;
    params.push(parseInt(limit));

    const result = await req.pool.query(query);

    const alerts = result.rows.map(row => ({
      id: row.metadata?.externalId || row.id,
      zoneId: row.zone_code,
      severity: alertSeverityDisplay(row.severity),
      type: row.alert_type === 'crew' ? 'Crew' : 'System',
      crewId: row.metadata?.crewId,
      title: row.title,
      description: row.message,
      eta: row.metadata?.eta || null,
      status: row.metadata?.status ?? alertStatus(row),
      timestamp: row.created_at instanceof Date ? row.created_at.toISOString() : row.created_at,
    }));

    res.json(alerts);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch alerts',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * @swagger
 * /api/alerts/{id}/ack:
 *   post:
 *     tags: [Alerts]
 *     summary: Acknowledge alert
 *     description: Mark an alert as acknowledged
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Alert ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               acknowledgedBy:
 *                 type: string
 *                 description: Name of person acknowledging
 *                 example: John Doe
 *     responses:
 *       200:
 *         description: Alert acknowledged successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 *                 message:
 *                   type: string
 *                   example: Alert acknowledged successfully
 */
router.post('/:id/ack', async (req, res) => {
  try {
    const { id } = req.params;
    const { acknowledgedBy } = req.body;

    const query = `
      UPDATE alerts
      SET acknowledged = true,
          acknowledged_at = NOW(),
          acknowledged_by = COALESCE($1, acknowledged_by),
          metadata = jsonb_set(
            metadata || '{}',
            '{status}',
            '"acknowledged"',
            true
          )
      WHERE id = $2
      RETURNING *
    `;

    const result = await req.pool.query(query, [acknowledgedBy, id]);

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: 'Alert not found',
        details: `Alert with ID ${id} does not exist`
      });
    }

    res.json({
      success: true,
      message: 'Alert acknowledged successfully',
      alert: {
        id: result.rows[0].id,
        acknowledged: true,
        acknowledgedAt: result.rows[0].acknowledged_at,
        acknowledgedBy: result.rows[0].acknowledged_by
      }
    });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to acknowledge alert',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;