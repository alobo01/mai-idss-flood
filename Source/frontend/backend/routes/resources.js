import { Router } from 'express';
import { parsePoint } from '../utils/helpers.js';

const router = Router();

/**
 * @swagger
 * /api/resources:
 *   get:
 *     tags: [Resources]
 *     summary: Get resources with optional filters
 *     description: Retrieve depots, equipment, and crews with optional filtering
 *     parameters:
 *       - in: query
 *         name: type
 *         schema:
 *           type: string
 *           enum: [depot, equipment, crew]
 *         description: Resource type filter
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *         description: Resource status filter
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 depots:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: string
 *                       name:
 *                         type: string
 *                       lat:
 *                         type: number
 *                       lng:
 *                         type: number
 *                 equipment:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: string
 *                       type:
 *                         type: string
 *                       subtype:
 *                         type: string
 *                       capacity_lps:
 *                         type: number
 *                       units:
 *                         type: number
 *                       depot:
 *                         type: string
 *                       status:
 *                         type: string
 *                 crews:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: string
 *                       name:
 *                         type: string
 *                       skills:
 *                         type: array
 *                         items:
 *                           type: string
 *                       depot:
 *                         type: string
 *                       status:
 *                         type: string
 *                       lat:
 *                         type: number
 *                       lng:
 *                         type: number
 */
router.get('/', async (req, res) => {
  try {
    const { type, status } = req.query;

    let query = `
      SELECT
        code,
        name,
        type,
        status,
        capacity,
        capabilities,
        contact_info,
        ST_AsGeoJSON(location, 6) as location
      FROM resources
    `;

    const params = [];
    const clauses = [];
    let paramIndex = 1;

    if (type) {
      clauses.push(`LOWER(type) = LOWER($${paramIndex++})`);
      params.push(type);
    }

    if (status) {
      clauses.push(`LOWER(status) = LOWER($${paramIndex++})`);
      params.push(status);
    }

    if (clauses.length > 0) {
      query += ` WHERE ${clauses.join(' AND ')}`;
    }

    query += ' ORDER BY type, name';

    const result = await req.pool.query(query, params);

    const payload = {
      depots: [],
      equipment: [],
      crews: []
    };

    result.rows.forEach(row => {
      const location = parsePoint(row.location);
      const capabilities = row.capabilities || {};

      if (row.type === 'depot') {
        payload.depots.push({
          id: row.code,
          name: row.name,
          lat: location.lat,
          lng: location.lng,
        });
        return;
      }

      if (row.type === 'equipment') {
        payload.equipment.push({
          id: row.code,
          type: capabilities.type || row.name,
          subtype: capabilities.subtype,
          capacity_lps: capabilities.capacity_lps,
          units: capabilities.units,
          depot: capabilities.depot,
          status: row.status,
        });
        return;
      }

      if (row.type === 'crew') {
        payload.crews.push({
          id: row.code,
          name: row.name,
          skills: capabilities.skills || [],
          depot: capabilities.depot,
          status: row.status,
          lat: location.lat,
          lng: location.lng,
        });
      }
    });

    res.json(payload);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch resources',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;