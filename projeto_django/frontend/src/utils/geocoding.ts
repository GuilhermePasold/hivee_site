export async function searchLocations(query: string): Promise<LocationResult[]> {
  if (!query) return [];
  
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
        query
      )}&format=json&countrycodes=br&limit=5`,
      {
        headers: {
          'Accept-Language': 'pt-BR',
        },
      }
    );
    
    if (!response.ok) throw new Error('Falha ao buscar localização');
    
    const data = await response.json();
    return data.map((item: any) => ({
      display_name: item.display_name,
      lat: item.lat,
      lon: item.lon,
    }));
  } catch (error) {
    console.error('Erro ao buscar localização:', error);
    return [];
  }
}