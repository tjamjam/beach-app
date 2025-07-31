// --- HELPER FUNCTIONS ---

// Translates wind degrees to a cardinal direction.
function getWindDirection(degrees) {
    if (degrees === null || degrees === undefined) return 'N/A';
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                       'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.round(degrees / 22.5) % 16];
}

// --- MAIN WORKER ---

export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        const path = url.pathname;
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Token',
        };

        // Handle pre-flight browser requests
        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        try {

            if (path === '/weather') {
                try {
                    const apiKey = env.OPENWEATHER_API_KEY; 
                    if (!apiKey) throw new Error("OpenWeatherMap API key is not configured.");

                    // --- UPDATED COORDINATES FOR ZIP CODE 05408 ---
                    const lat = 44.51;
                    const lon = -73.24;
                    
                    const currentUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}`;
                    const forecastUrl = `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${apiKey}`;

                    const [currentResponse, forecastResponse] = await Promise.all([
                        fetch(currentUrl),
                        fetch(forecastUrl)
                    ]);

                    if (!currentResponse.ok) throw new Error(`Current Weather API failed with status ${currentResponse.status}`);
                    if (!forecastResponse.ok) throw new Error(`Forecast API failed with status ${forecastResponse.status}`);

                    const currentData = await currentResponse.json();
                    const forecastData = await forecastResponse.json();

                    // Process current weather
                    const currentFormatted = {
                        temperature: ((currentData.main.temp - 273.15) * 9/5 + 32).toFixed(0),
                        windSpeed: (currentData.wind.speed * 2.237).toFixed(0),
                        windDirection: getWindDirection(currentData.wind.deg),
                        conditions: currentData.weather[0] ? currentData.weather[0].main : "Clear",
                        humidity: currentData.main.humidity,
                        // --- UPDATED STATION NAME FOR CLARITY ---
                        station: { name: "New North End (05408)", coordinates: { lat: currentData.coord.lat, lon: currentData.coord.lon } },
                        timestamp: new Date(currentData.dt * 1000).toLocaleString('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: 'numeric', hour12: true }),
                        icon: `https://openweathermap.org/img/wn/${currentData.weather[0].icon}@4x.png` // Using the large @4x icon
                    };

                    // Process hourly forecast
                    const hourlyFormatted = forecastData.list.slice(0, 3).map(hour => ({
                        time: new Date(hour.dt * 1000).toLocaleString('en-US', { timeZone: 'America/New_York', hour: 'numeric', hour12: true }),
                        temp: ((hour.main.temp - 273.15) * 9/5 + 32).toFixed(0),
                        icon: `https://openweathermap.org/img/wn/${hour.weather[0].icon}@2x.png`,
                        description: hour.weather[0].description
                    }));

                    // Combine into the final data package
                    const finalData = {
                        current: currentFormatted,
                        hourly: hourlyFormatted
                    };

                    return new Response(JSON.stringify(finalData), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });

                } catch (error) {
                    console.error('Weather fetch error:', error);
                    return new Response(JSON.stringify({ error: 'Weather service temporarily unavailable', details: error.message }), { status: 503, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                }
            }


            // --- AIR QUALITY ENDPOINT (Aligned with AirNow Category Numbers) ---
            if (path === '/air-quality') {
                try {
                    const apiKey = env.AIRNOW_API_KEY;
                    if (!apiKey) throw new Error("AirNow API key is not configured.");

                    const zipCode = "05401";
                    const airNowUrl = `https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=${zipCode}&distance=25&API_KEY=${apiKey}`;
                    
                    const response = await fetch(airNowUrl);
                    if (!response.ok) throw new Error(`AirNow API returned ${response.status}`);

                    const data = await response.json();
                    if (!data || data.length === 0) throw new Error("No data returned from AirNow.");

                    const overallAqi = data.reduce((maxAqi, p) => Math.max(maxAqi, p.AQI), 0);
                    const mainPollutantData = data.find(p => p.AQI === overallAqi) || data[0];
                    const category = mainPollutantData.Category;

                    // --- THIS IS THE NEW, SIMPLER FORMAT ---
                    const formattedData = {
                        aqi: overallAqi,
                        text: category.Name,
                        advice: `The current air quality is ${category.Name}.`,
                        // We now pass the raw category number directly.
                        categoryNumber: category.Number, 
                        pollutants: {
                            pm2_5: data.find(p => p.ParameterName === "PM2.5")?.Value || 0,
                        }
                    };

                    return new Response(JSON.stringify(formattedData), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });

                } catch (error) {
                    console.error('Air Quality fetch error:', error);
                    return new Response(JSON.stringify({ error: 'Air Quality data unavailable', details: error.message }), { status: 503, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                }
            }


            // --- EMAIL SUBSCRIBE ENDPOINT ---
            if (path === '/subscribe' && request.method === 'POST') {
                try {
                    const body = await request.json();
                    const email = body.email;
                    if (!email) throw new Error('Email is required');
                    await env.SUBSCRIBERS.put(email, 'true');
                    return new Response(JSON.stringify({ message: 'Successfully subscribed!', email: email }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                } catch (error) {
                    console.error('Subscription error:', error);
                    return new Response(JSON.stringify({ error: 'Subscription failed', details: error.message }), { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                }
            }

            // --- GET SUBSCRIBERS ENDPOINT ---
            if (path === '/get-subscribers' && request.method === 'GET') {
                try {
                    const providedToken = request.headers.get('X-API-Token');
                    if (providedToken !== env.CF_API_TOKEN) throw new Error('Unauthorized');
                    const listResult = await env.SUBSCRIBERS.list();
                    const emails = listResult.keys.map(key => key.name);
                    return new Response(JSON.stringify({ subscribers: emails }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                } catch (error) {
                    return new Response(JSON.stringify({ error: 'Authorization failed', details: error.message }), { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
                }
            }

            // Fallback for any other path
            return new Response(JSON.stringify({ error: 'Endpoint not found.' }), { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });

        } catch (error) {
            console.error('Worker uncaught error:', error);
            return new Response(JSON.stringify({ error: 'An unexpected server error occurred.', details: error.message }), { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
        }
    }
};
