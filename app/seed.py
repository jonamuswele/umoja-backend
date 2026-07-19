import json
import datetime
from app.database import SessionLocal, engine, Base
from app import models

# Drop and recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 1. Seed Users
    owners_list = ["kenya_owner", "nigeria_owner", "drc_owner", "namibia_owner", "chad_owner"]
    users_to_add = [
        models.User(username="admin", password_hash="admin", role="admin")
    ]
    for username in owners_list:
        users_to_add.append(models.User(username=username, password_hash="umoja", role="owner"))
        
    db.add_all(users_to_add)
    db.commit()

    # 2. Seed Countries
    countries_data = [
        {
            "id": "kenya",
            "name": "Kenya",
            "motto": "The Cradle of Humanity & Innovation",
            "accent": "#D27D2D",
            "desc": "Renowned for its breathtaking Savannahs, the majestic Rift Valley, the vibrant technological ecosystem of Nairobi (Silicon Savannah), and pristine white-sand beaches in Diani. Buying land in Kenya connects you with East Africa's leading economic and tourism powerhouse.",
            "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
            "highlights": ["Silicon Savannah Tech Hub", "Maasai Mara Wild Migration", "Robust Digitized Land Registry"],
            "potential_neighborhoods": [
                { "img": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&q=80", "caption": "Premium green suburbs of Karen & Runda" },
                { "img": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=600&q=80", "caption": "Palm-fringed holiday estates in Diani Beach" }
            ],
            "culture_info": {
                "whyLive": "Live here for the perfect balance of a booming tech-driven economy (Silicon Savannah) and world-renowned natural beauty. The local climate is year-round spring-like weather with warm, sunny days.",
                "bestBuild": "Coastal Arched Villas in Diani or modern stone-finish ecological lodges in Nanyuki. Rammed earth construction using red volcanic soil is highly sustainable and matches the red African backdrop.",
                "culture": "Warm, welcoming, and community-centric. Swahili culture emphasizes hospitality (Karibu) and collective action (Harambee), fostering great neighborhood integration.",
                "culturePhotos": [
                    { "img": "https://images.unsplash.com/photo-1489440543286-a69330151c0b?w=800&q=80", "rotate": -3.5, "scale": 1, "caption": "Community gathering and Swahili traditions" },
                    { "img": "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800&q=80", "rotate": 2.5, "scale": 0.9, "caption": "Local architectural details & warm earth tones" }
                ]
            }
        },
        {
            "id": "drc",
            "name": "DRC (Congo)",
            "motto": "The Heartbeat of the Continent",
            "accent": "#1A3E26",
            "desc": "A land of unparalleled natural abundance, from the mighty Congo River to the world's second-largest rainforest. Urban centers like Kinshasa and Lubumbashi are expanding rapidly, presenting exceptional opportunities for residential and commercial real estate development in prime hubs.",
            "video_url": "https://www.w3schools.com/html/movie.mp4",
            "highlights": ["Kinshasa Urban Expansion", "Congo River Scenic Waterfronts", "Rich Soil & Agricultural Potential"],
            "potential_neighborhoods": [
                { "img": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80", "caption": "Riverside properties along the Congo River" },
                { "img": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&q=80", "caption": "Upscale residential enclaves in Golf, Lubumbashi" }
            ],
            "culture_info": {
                "whyLive": "Unparalleled natural wealth and biodiversity. The Congo River provides a scenic waterfront backdrop, and rapid urban growth presents exceptional investment and agricultural opportunities.",
                "bestBuild": "High-thermal-mass Rammed Earth Pavilions or modern brick waterfront residences. Heavy brick structures insulate against the tropical climate, using regional clay for cooling ventilation.",
                "culture": "Vibrant, creative, and musically rich. The people of Congo are famous for their unmatched artistic expression, legendary Soukous music, and the elegant Sapeurs fashion culture.",
                "culturePhotos": [
                    { "img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&q=80", "rotate": -2.8, "scale": 1, "caption": "Vibrant Congolese musical rhythm and artistic crafts" },
                    { "img": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80", "rotate": 2.0, "scale": 0.92, "caption": "Riverside design inspiration using local materials" }
                ]
            }
        },
        {
            "id": "namibia",
            "name": "Namibia",
            "motto": "Ethereal Landscapes & Absolute Stability",
            "accent": "#D27D2D",
            "desc": "A country of dramatic contrasts, where the Namib Desert meets the wild Atlantic Ocean. Highly secure land titles, excellent infrastructure, and a quiet, law-abiding lifestyle make Namibia one of the safest hubs for physical land ownership in southern Africa.",
            "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
            "highlights": ["Highly Secure Land Registry", "Swakopmund Coastline Living", "Ecotourism Hub"],
            "potential_neighborhoods": [
                { "img": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&q=80", "caption": "Mountain valley layouts in Windhoek Estates" },
                { "img": "https://images.unsplash.com/photo-1599809228728-5a0eebf9c55b?w=600&q=80", "caption": "Clean streets of coastal Swakopmund" }
            ],
            "culture_info": {
                "whyLive": "Unrivaled peace, safety, and absolute legal stability. Perfect for those looking for clean desert breezes, spectacular dune landscapes, and highly developed modern infrastructure.",
                "bestBuild": "Rammed Earth Oasis designs using desert sand, or solar-passive desert pavilions. Structures require thick earthen walls to regulate the high desert heat during the day and capture warmth at night.",
                "culture": "A peaceful, law-abiding community with a rich tapestry of Nama, Herero, and Ovambo traditions. The local way of life values conservation, quiet wilderness, and peaceful co-existence.",
                "culturePhotos": [
                    { "img": "https://images.unsplash.com/photo-1516026672322-bc52d61a5537?w=800&q=80", "rotate": 2.0, "scale": 1, "caption": "Tranquil desert sandscapes and architecture" },
                    { "img": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=800&q=80", "rotate": -3.0, "scale": 0.88, "caption": "Ecotourism design using local wood and stone structures" }
                ]
            }
        },
        {
            "id": "chad",
            "name": "Chad (Tchad)",
            "motto": "The Soul of the Sahel",
            "accent": "#1A3E26",
            "desc": "A nation defined by the stunning Sahara sandstone monoliths of Ennedi, historic trade routes, and a deep culture of community. Investing in Chad offers early-market advantages in the fast-urbanizing capital N'Djamena, where infrastructure development is surging.",
            "video_url": "https://www.w3schools.com/html/movie.mp4",
            "highlights": ["Early Market Appreciation", "N'Djamena Commercial Core", "Rich Sahelian Heritage"],
            "potential_neighborhoods": [
                { "img": "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=600&q=80", "caption": "Sun-drenched courtyard home designs" },
                { "img": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&q=80", "caption": "Rapidly expanding residential avenues in Chagoua" }
            ],
            "culture_info": {
                "whyLive": "Live here for an authentic Sahelian experience and early-market investment gains in N'Djamena. A region of historical trans-Saharan trade routes, sandstone monoliths, and vast open skies.",
                "bestBuild": "Adobe Earth-block vaults or courtyard-style adobe homesteads. Thick loam walls and central courtyard designs keep houses cool in the dry, warm Sahel climate without active air conditioning.",
                "culture": "Deeply collaborative and resilient. The Sahelian heritage is grounded in pastoral community ties, traditional horse racing, and high respect for family and elders.",
                "culturePhotos": [
                    { "img": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80", "rotate": -3.5, "scale": 1, "caption": "Sahelian community values and mud architecture" },
                    { "img": "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=800&q=80", "rotate": 2.1, "scale": 0.92, "caption": "Traditional courtyard home styling" }
                ]
            }
        },
        {
            "id": "nigeria",
            "name": "Nigeria",
            "motto": "The Giant of Africa",
            "accent": "#D27D2D",
            "desc": "Africa's economic heartbeat and largest population. The Lekki-Epe corridor in Lagos and the planned districts of Abuja represent some of the highest-growth land value zones in the world. Secure land titles here guarantee long-term wealth appreciation.",
            "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
            "highlights": ["Epe-Lekki High Appreciation Corridor", "Abuja Serene Diplomatic Enclaves", "High Rental Market Yields"],
            "potential_neighborhoods": [
                { "img": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=600&q=80", "caption": "Gated estate villas in Lekki-Epe, Lagos" },
                { "img": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&q=80", "caption": "Modern valley residences in Kuje, Abuja" }
            ],
            "culture_info": {
                "whyLive": "The economic giant of Africa. Live here to tap into the continent's largest digital hub, high-energy trade, and a booming middle-class real estate market with exceptional investment growth.",
                "bestBuild": "Contemporary concrete-frame estates or modern eco-pavilions with wide overhanging roofs. Structures must incorporate elevated foundations for seasonal rains and deep solar shading layouts.",
                "culture": "Lively, ambitious, and globally influential. Nigeria is the powerhouse of Nollywood, Afrobeat music, and vibrant fashion. The culture is energetic, enterprising, and highly celebratory.",
                "culturePhotos": [
                    { "img": "https://images.unsplash.com/photo-1596436889106-be35e843f974?w=800&q=80", "rotate": 2.8, "scale": 1, "caption": "Vibrant Lagos fashion and energetic Afrobeat spaces" },
                    { "img": "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800&q=80", "rotate": -1.5, "scale": 0.9, "caption": "Modern tropical villa and shaded balcony architecture" }
                ]
            }
        }
    ]

    for c in countries_data:
        db.add(models.Country(
            id=c["id"],
            name=c["name"],
            motto=c["motto"],
            accent=c["accent"],
            desc=c["desc"],
            video_url=c["video_url"],
            highlights=json.dumps(c["highlights"]),
            potential_neighborhoods=json.dumps(c["potential_neighborhoods"]),
            culture_info=json.dumps(c["culture_info"])
        ))
    db.commit()

    # 3. Seed Plots
    plots_data = [
        {
            "id": "ke-nanyuki",
            "country_id": "kenya",
            "title": "Nanyuki Savannah Foothills",
            "size": "50m x 40m (2,000 SQM)",
            "neighborhood": "Located in a secure gated community just 15 minutes outside Nanyuki town. The neighborhood is rich in acacia woodlands, featuring panoramic views of Mt. Kenya's snow peaks and neighbors a local wildlife conservancy. Pre-installed electricity and clean borehole water connections are fully certified.",
            "price": 32000.0,
            "owner_username": "kenya_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800&q=80", "rotate": -3.5, "scale": 1, "caption": "Acacia woodlands surrounding the estate" },
                { "img": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80", "rotate": 2.1, "scale": 0.92, "caption": "View of the actual flat, surveyed plot" }
            ]
        },
        {
            "id": "ke-diani",
            "country_id": "kenya",
            "title": "Diani Coastal Breezes",
            "size": "30m x 25m (750 SQM)",
            "neighborhood": "Situated in a peaceful, upscale residential enclave in Diani, only a 10-minute walk from the world-famous white sandy shores. The surrounding area features lush coconut palms, boutique lodges, and smooth access roads. Perfect for building a premium holiday villa or a retirement sanctuary.",
            "price": 48000.0,
            "owner_username": "kenya_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80", "rotate": 2.8, "scale": 1, "caption": "Quiet coastal access path to the beach nearby" },
                { "img": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=800&q=80", "rotate": -1.5, "scale": 0.9, "caption": "The cleared plot terrain ready for construction" }
            ]
        },
        {
            "id": "drc-kinkole",
            "country_id": "drc",
            "title": "Kinshasa Riverbend Estate",
            "size": "40m x 30m (1,200 SQM)",
            "neighborhood": "Located in Kinkole's scenic riverside area, offering fresh breezes off the Congo River and a tranquil atmosphere away from Central Kinshasa. The local area features artisanal fish markets, riverside restaurants, and a developing green belt. Soil is highly stable and prepared for multi-story residential building.",
            "price": 28000.0,
            "owner_username": "drc_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1489440543286-a69330151c0b?w=800&q=80", "rotate": -2.2, "scale": 1, "caption": "Congo River bank and lush canopy close to site" },
                { "img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&q=80", "rotate": 1.9, "scale": 0.91, "caption": "The surveyed plot boundary marker" }
            ]
        },
        {
            "id": "drc-lubumbashi",
            "country_id": "drc",
            "title": "Lubumbashi Golf Extension",
            "size": "35m x 30m (1,050 SQM)",
            "neighborhood": "Vetted land in the peaceful, high-end Golf District extension of Lubumbashi. Safe streets, paved road access, and pre-connected grids make this one of the most stable investments in the Katanga province. The neighborhood boasts modern villas, private schools, and recreational parks.",
            "price": 35000.0,
            "owner_username": "drc_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&q=80", "rotate": -3.0, "scale": 1, "caption": "Modern streetscape in the neighboring residential sector" },
                { "img": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80", "rotate": 2.5, "scale": 0.88, "caption": "Bare land plot showing rich, flat Katanga soil" }
            ]
        },
        {
            "id": "na-swakop",
            "country_id": "namibia",
            "title": "Swakopmund Dunes & Sea Vista",
            "size": "30m x 20m (600 SQM)",
            "neighborhood": "Located in the quiet suburban coastal zone of Swakopmund, with the Namib dunes on one side and the Atlantic ocean breeze on the other. Extremely clean municipal services, reliable water, paved roads, and walking distance to beachfront boardwalks. Highly attractive for Airbnb developments.",
            "price": 42000.0,
            "owner_username": "namibia_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1516026672322-bc52d61a5537?w=800&q=80", "rotate": 2.0, "scale": 1, "caption": "Namib desert coastal landscape neighboring the suburb" },
                { "img": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=800&q=80", "rotate": -3.0, "scale": 0.88, "caption": "Direct view of the cleared plot corner" }
            ]
        },
        {
            "id": "na-elisenheim",
            "country_id": "namibia",
            "title": "Windhoek Elisenheim Estate",
            "size": "25m x 20m (500 SQM)",
            "neighborhood": "Nestled in the mountain valleys of Elisenheim Lifestyle Estate, just north of Windhoek. Features 24/7 security patrol, child-friendly parks, a community shopping center, and absolute quietness. An ideal plot for family homes or high-yield rental townhouses.",
            "price": 26000.0,
            "owner_username": "namibia_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80", "rotate": -1.8, "scale": 1, "caption": "Beautiful mountain views surrounding the valley estate" },
                { "img": "https://images.unsplash.com/photo-1533240332313-0db49b439ad3?w=800&q=80", "rotate": 2.4, "scale": 0.9, "caption": "The surveyed plot showing boundary coordinates" }
            ]
        },
        {
            "id": "td-chagoua",
            "country_id": "chad",
            "title": "N'Djamena Chagoua Hub",
            "size": "30m x 30m (900 SQM)",
            "neighborhood": "Situated in N'Djamena's rapidly developing Chagoua district, adjacent to new commercial centers and near the Chari River. Fertile grounds, rising local valuations, and friendly community layout make this plot ideal for a family homestead with structural resilience.",
            "price": 18000.0,
            "owner_username": "chad_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80", "rotate": -3.5, "scale": 1, "caption": "Sahelian community values and mud architecture" },
                { "img": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80", "rotate": 2.1, "scale": 0.92, "caption": "View of the actual flat, surveyed plot" }
            ]
        },
        {
            "id": "ng-epe",
            "country_id": "nigeria",
            "title": "Epe New Horizon Estate",
            "size": "30m x 20m (600 SQM)",
            "neighborhood": "Vetted dry land situated in a gated layout along the Lekki-Epe corridor, Lagos. The surrounding area is seeing explosive development, including the new Lekki international airport zone. Clean paved roads, streetlights, and 24/7 security. Title: Certificate of Occupancy (C of O).",
            "price": 22000.0,
            "owner_username": "nigeria_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1596436889106-be35e843f974?w=800&q=80", "rotate": 2.8, "scale": 1, "caption": "Lush palm-lined boulevard at the estate entrance" },
                { "img": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=800&q=80", "rotate": -1.5, "scale": 0.9, "caption": "Flat dry plot terrain with clear beacons" }
            ]
        },
        {
            "id": "ng-kuje",
            "country_id": "nigeria",
            "title": "Abuja Kuje Green Valley",
            "size": "40m x 25m (1,000 SQM)",
            "neighborhood": "Located in the quiet and scenic valley of Kuje, Abuja. The neighborhood features serene mountain backdrops, fresh air, private security guards, and modern family homesteads. An excellent investment for a spacious luxury home or agricultural garden compound.",
            "price": 29000.0,
            "owner_username": "nigeria_owner",
            "photos": [
                { "img": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=800&q=80", "rotate": -2.2, "scale": 1, "caption": "Panoramic scenic landscape around the Kuje hills" },
                { "img": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&q=80", "rotate": 1.9, "scale": 0.91, "caption": "The secure plot perimeter boundary" }
            ]
        }
    ]

    for p in plots_data:
        db.add(models.Plot(
            id=p["id"],
            country_id=p["country_id"],
            title=p["title"],
            size=p["size"],
            price=p["price"],
            neighborhood=p["neighborhood"],
            owner_username=p["owner_username"],
            photos=json.dumps(p["photos"])
        ))
    db.commit()

    # 4. Seed Clicks / Views (distributed over the last 7 days)
    today = datetime.datetime.utcnow()
    views_distributions = {
        "ke-nanyuki": [12, 18, 25, 20, 22, 28, 17],  # 7 days views distribution
        "ke-diani": [8, 12, 15, 14, 16, 20, 13],
        "drc-kinkole": [5, 6, 8, 7, 9, 12, 8],
        "drc-lubumbashi": [10, 12, 14, 13, 11, 15, 12],
        "na-swakop": [15, 16, 18, 20, 22, 25, 18],
        "na-elisenheim": [6, 8, 9, 7, 8, 10, 8],
        "td-chagoua": [4, 5, 6, 5, 7, 8, 5],
        "ng-epe": [20, 24, 30, 28, 35, 42, 38],
        "ng-kuje": [12, 15, 18, 16, 20, 22, 18]
    }

    for plot_id, dist in views_distributions.items():
        for days_ago, count in enumerate(dist):
            date = today - datetime.timedelta(days=6-days_ago)
            for _ in range(count):
                db.add(models.PlotView(plot_id=plot_id, timestamp=date))
    db.commit()

    # 5. Seed Inquiries
    inquiries_data = [
        {
            "id": "inq-284918",
            "plot_id": "ke-nanyuki",
            "full_name": "Fatoumata Diallo",
            "email": "fdiallo@safari.com",
            "phone": "+254 712 345 678",
            "current_city": "Dakar, Senegal",
            "message": "I am highly interested in the foothills plot near Mt. Kenya. Can we arrange a virtual land inspection next week? I have my escrow agent ready.",
            "type": "Negotiate",
            "timestamp": today - datetime.timedelta(hours=4)
        },
        {
            "id": "inq-942851",
            "plot_id": "ke-nanyuki",
            "full_name": "David Mensah",
            "email": "david.mensah@ghana-invest.com",
            "phone": "+233 20 123 4567",
            "current_city": "Accra, Ghana",
            "message": "Looks like a beautiful flat land. I would like to buy this securely. Please send the certified land registry title details for verification.",
            "type": "Buy",
            "timestamp": today - datetime.timedelta(days=1)
        },
        {
            "id": "inq-728103",
            "plot_id": "ke-diani",
            "full_name": "Sarah Jenkins",
            "email": "sjenkins@uk-diaspora.co.uk",
            "phone": "+44 7911 123456",
            "current_city": "London, UK",
            "message": "Is this parcel close enough to Diani Beach to hear the ocean? I'm looking to build a sustainable retirement cottage. Send full escrow paperwork.",
            "type": "Buy",
            "timestamp": today - datetime.timedelta(days=2)
        },
        {
            "id": "inq-849102",
            "plot_id": "ng-epe",
            "full_name": "Chinedu Okafor",
            "email": "chinedu@abuja-law.com",
            "phone": "+234 803 111 2222",
            "current_city": "Abuja, Nigeria",
            "message": "I am proposing $20,000 for immediate transfer. My escrow lawyer will verify the C of O (Certificate of Occupancy) immediately.",
            "type": "Negotiate",
            "timestamp": today - datetime.timedelta(hours=2)
        }
    ]

    for inq in inquiries_data:
        db.add(models.Inquiry(
            id=inq["id"],
            plot_id=inq["plot_id"],
            full_name=inq["full_name"],
            email=inq["email"],
            phone=inq["phone"],
            current_city=inq["current_city"],
            message=inq["message"],
            type=inq["type"],
            timestamp=inq["timestamp"]
        ))
    db.commit()

    print("Database successfully created and seeded with high-fidelity records!")

finally:
    db.close()
