import { Router } from 'express';

const router = Router();

/**
 * @swagger
 * /api/zones:
 *   get:
 *     tags: [Zones]
 *     summary: Get zones as GeoJSON
 *     description: Retrieve all zones formatted as a GeoJSON FeatureCollection
 *     responses:
 *       200:
 *         description: Successful response
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 type:
 *                   type: string
 *                   example: FeatureCollection
 *                 features:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       type:
 *                         type: string
 *                         example: Feature
 *                       geometry:
 *                         type: object
 *                       properties:
 *                         type: object
 *                         properties:
 *                           id:
 *                             type: string
 *                           name:
 *                             type: string
 *                           population:
 *                             type: number
 *                           critical_assets:
 *                             type: array
 *                             items:
 *                               type: string
 *       500:
 *         description: Server error
 */
router.get('/', async (req, res) => {
  try {
    const query = `
      SELECT
        id,
        code,
        name,
        description,
        population,
        area_km2,
        admin_level,
        critical_assets,
        ST_AsGeoJSON(geometry, 6) as geometry
      FROM zones
      ORDER BY name
    `;

    const result = await req.pool.query(query);

    const features = result.rows.map(row => ({
      type: 'Feature',
      geometry: JSON.parse(row.geometry),
      properties: {
        id: row.code,
        name: row.name,
        description: row.description,
        population: row.population,
        critical_assets: row.critical_assets || [],
        admin_level: row.admin_level || 10,
      }
    }));

    const geoJson = {
      type: 'FeatureCollection',
      features
    };

    res.json(geoJson);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({
      error: 'Failed to fetch zones',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;