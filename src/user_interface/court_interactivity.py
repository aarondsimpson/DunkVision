#STEP ONE
#Created to handle UI click plumbing and will contain click binding
#On click: get cx, cy for canvas click coordinates, reject if they're in the letter box margin.
#Convert to native image coordinates, ix, iy. Pass these coordiantes to application_logic.zoning/zoning_configuration. 
#STEP TWO IN ZONE CONFIG

#STEP SIX 
#Get distance via pixels_to_feet(), get zone via get_zone(). Return (distance_feet, zone_data) to CourtFrame. 
#STEP SEVEN 
#in court_frames.py: StatusBar: "Recorded Shot: {zone_name}, {distance_ft:.1f} ft"
#STEP EIGHT
#Build unit testing folder and files for unit tests? Otherwise test court coordinate mapping and every zone. 
#STEP NINE
#Build dev_tools, overlays for UI masks