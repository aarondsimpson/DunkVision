#STEP THREE
#def pixels_to_feet(ix, iy): convert ix, iy to dx, dy from hoop center in feet. 
#Compute Euclidean distance sqrt(dx*dx + dy*dy), return: distance_feet, dx_ft, dy_ft). 
#STEP FOUR IN ZONING CONFIG AFTER BUILDING MASKS (BUILD MASKS FOR NO CLICK ZONE)

#STEP FIVE
#Load masks as PIL.Image -> .load() pixel array. 
'''def get_zone(ix, iy)
    color=mask_pixels[ix, iy][:3]
    return ZONE_MAP.get(color, {"name": "Unknown", "is_3_point": None})
'''
#STEP SIX IN COURT_INTERACTIVITY