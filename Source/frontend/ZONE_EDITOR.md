# GeoJSON Zone Editor

A comprehensive, interactive zone editor for managing flood prediction zones in the flood prediction system.

## Features

### 🗺️ **Interactive Map-Based Editing**
- **Drawing Tools**: Create new zones using polygon and rectangle drawing tools
- **Real-time Editing**: Modify existing zone boundaries with intuitive drag controls
- **Visual Feedback**: Selected zones are highlighted with distinct styling
- **Map Navigation**: Full OpenStreetMap integration with zoom and pan controls

### 📝 **Zone Property Management**
- **Zone Identification**: Unique ID generation with customizable naming
- **Population Data**: Configure population counts for each zone
- **Critical Assets**: Manage lists of critical infrastructure (hospitals, schools, etc.)
- **Administrative Levels**: Set hierarchical admin levels for zone organization

### 📁 **Import/Export Functionality**
- **GeoJSON Import**: Load zone data from standard GeoJSON files
- **GeoJSON Export**: Save zones to properly formatted GeoJSON files
- **Validation**: Comprehensive validation of imported data structure and content

### ✅ **Real-time Validation**
- **Zone ID Validation**: Ensures unique, properly formatted zone identifiers
- **Property Validation**: Validates population numbers, admin levels, and asset names
- **Geometry Validation**: Ensures proper GeoJSON structure and polygon geometry
- **Import Validation**: Comprehensive validation of imported GeoJSON files

## Architecture

### Component Structure
```
src/components/ZoneEditor.tsx     # Main zone editor component
├── Zone List Sidebar              # Zone list with edit/delete actions
├── Interactive Map                # Leaflet-based map with drawing tools
└── Properties Panel               # Zone property editing forms
```

### Technology Stack
- **React 18** with TypeScript
- **React-Leaflet** for map integration
- **Leaflet-Draw** for drawing and editing tools
- **shadcn/ui** component library
- **Zod** for type-safe data validation
- **Tailwind CSS** for styling

### Data Model
```typescript
interface ZoneProperties {
  id: string;                    // Unique zone identifier
  name: string;                  // Human-readable zone name
  population: number;            // Population count
  critical_assets: string[];     // List of critical infrastructure
  admin_level: number;           // Administrative hierarchy level
}
```

## Usage

### Administrator Interface
The zone editor is integrated into the Administrator role interface at `/admin/regions`:

1. **Navigate**: Login as Administrator → Regions Manager
2. **Load**: Existing zones are automatically loaded from `/mock/zones.geojson`
3. **Edit**: Click zones to select and edit their properties
4. **Draw**: Use "Draw Zone" button to create new zones
5. **Import**: Click "Import" to load GeoJSON files
6. **Export**: Click "Export" to save current zones to file

### Drawing New Zones
1. Click the "Draw Zone" button in the map header
2. Select either polygon or rectangle drawing tool from the map controls
3. Draw the zone boundary on the map
4. The new zone will be automatically created and selected for property editing
5. Configure zone properties in the properties panel
6. Click "Save" to apply changes

### Editing Zone Properties
1. Click on a zone in the list or on the map to select it
2. Click the "Edit Zone" button in the properties panel
3. Modify zone properties:
   - **Zone Name**: Human-readable name for the zone
   - **Zone ID**: Unique identifier (editable only for new zones)
   - **Population**: Number of residents in the zone
   - **Admin Level**: Hierarchical administrative level (1-15)
   - **Critical Assets**: List of important infrastructure locations
4. Click "Save" to apply changes or "Cancel" to discard

### Importing Zones
1. Click the "Import" button in the zones list header
2. Select a valid GeoJSON file (.json or .geojson extension)
3. The file will be validated automatically:
   - Must be a valid GeoJSON FeatureCollection
   - All features must be polygons
   - Zone properties must be valid
   - Zone IDs must be unique
4. Valid zones will replace the current zone set
5. Validation errors will be displayed if the file is invalid

### Exporting Zones
1. Click the "Export" button in the zones list header
2. The current zones will be downloaded as a GeoJSON file
3. File will be named with current date: `zones-YYYY-MM-DD.geojson`
4. File can be imported back into the editor or used in other GIS tools

## Validation Rules

### Zone ID Validation
- Required field
- Must start with a letter
- Can contain letters, numbers, underscores, and hyphens
- Must be unique across all zones
- Examples: `Z-ALFA`, `north_zone`, `sector-1`

### Zone Properties Validation
- **Name**: Required, non-empty string
- **Population**: Non-negative integer
- **Admin Level**: Integer between 1 and 15
- **Critical Assets**: No empty strings in asset list

### GeoJSON Validation
- Must be `FeatureCollection` type
- All features must be `Feature` type
- Geometry must be `Polygon` type
- Coordinates must be valid polygon coordinates
- Properties must include all required fields

## File Format

### Valid GeoJSON Structure
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "Z-ALFA",
        "name": "Riverside North",
        "population": 12450,
        "critical_assets": ["Hospital HN1", "School SN3"],
        "admin_level": 10
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-3.71, 40.41],
          [-3.70, 40.41],
          [-3.70, 40.42],
          [-3.71, 40.42],
          [-3.71, 40.41]
        ]]
      }
    }
  ]
}
```

## Error Handling

The zone editor includes comprehensive error handling:

### Validation Errors
- Displayed prominently with red styling
- Clear error messages explaining validation failures
- Dismiss button to clear errors after fixing issues
- Callback function to notify parent components of errors

### Load Errors
- Graceful handling of zone data loading failures
- Error messages displayed to user
- Retry mechanism through page refresh

### Import Errors
- Detailed validation error reporting for each feature
- File format validation with helpful error messages
- No data corruption - invalid files are rejected safely

## Integration

### Component Props
```typescript
interface ZoneEditorProps {
  initialZones?: GeoJSONType;           // Initial zone data
  onZonesChange?: (zones: GeoJSONType) => void;  // Change callback
  onValidationError?: (errors: string[]) => void;  // Error callback
  className?: string;                   // Additional CSS classes
}
```

### Usage Example
```typescript
import { ZoneEditor } from '@/components/ZoneEditor';

function AdminPage() {
  const handleZonesChange = (zones) => {
    // Save zones to backend
    console.log('Zones updated:', zones);
  };

  const handleErrors = (errors) => {
    // Handle validation errors
    console.error('Validation errors:', errors);
  };

  return (
    <ZoneEditor
      initialZones={initialData}
      onZonesChange={handleZonesChange}
      onValidationError={handleErrors}
    />
  );
}
```

## Dependencies

### Required Packages
- `leaflet` ^1.9.4
- `react-leaflet` ^4.2.1
- `leaflet-draw` ^1.0.4
- `@types/leaflet` ^1.9.21
- `@types/leaflet-draw` ^1.0.11

### Development Dependencies
- `@radix-ui/react-label` ^2.0.2
- `class-variance-authority` ^0.7.0
- `lucide-react` ^0.294.0

## Browser Compatibility

The zone editor supports all modern browsers:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Performance Considerations

- **Large Zone Sets**: Handles hundreds of zones efficiently
- **Map Rendering**: Uses Leaflet's optimized tile rendering
- **Real-time Validation**: Efficient validation with debounced updates
- **Memory Management**: Proper cleanup of map event listeners

## Future Enhancements

Potential improvements for future versions:
- **Layer Management**: Support for multiple zone layers
- **Advanced Drawing**: Support for complex polygon operations
- **Collaboration**: Real-time collaborative editing
- **Undo/Redo**: Full edit history management
- **Geocoding**: Address-based zone creation
- **Analytics**: Zone population and area calculations
- **Import Formats**: Support for additional GIS file formats (Shapefile, KML)