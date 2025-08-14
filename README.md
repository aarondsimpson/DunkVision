<h1>Dunk Vision</h1>

Dunk Vision is a desktop basketball shot tracker and data capture tool built using Python and tkinter. Designed for youth coaches, players, and parents, it lets users track, visualize, and analyze shot data to improve individual and team performance as well as direct training efforts. For courtside users, data can be exported for later analysis.

<h2> Rationale </h2>

Supporting my stepson through middle school basketball, summer camps, youth leagues, and high school basketball it became clear that youth organizations for basketball are propped up by limited funding, parent support, over-stretched coaches, and the goodwill of local communities.

Jerseys often escape the budget. Lunch is often brought by generous turn-taking parents. Training is often last-minute and inconsistent as coaches balance their personal lives.

Despite the enthusiasm to participate in this community, I was met with frustration to see my stepson receiving less support than was paid to receive. For this reason, I wanted to build a tool that would turn wild pickup games into structured, targeted training sessions based on the strengths and weaknesses of their previous performances beyond memory or guesswork. I wanted a tool that would support busy coaches to react to the patterns and trends that were missed while juggling parent politics. I wanted a tool that would turn our team that was winning 1 out of every 5 games into a team that stood a chance of winning every time they stepped on the court.

<h2>Screenshots</h2>

_pending development_

<h2>Features</h2>

<h3>🤾‍♂️ Player Management</h3>

1. Default player profiles based on basketball positions, such as 'Small Forward' and 'Point Guard'
2. Custom player profiles based on user definition to change 'Small Forward' to 'John Smith'
3. Switching between player profiles during sessions to track multiple players across both teams

<h3>🏀 Game Management</h3>

1. Users can select the quarter in which they are recording shots
2. Users can mark the game as finished to end the data collection process
3. Court will be zoned into 2pt and 3pt areas
4. Court will be zoned into strategic zones, such as 'Left Slot' or 'Top of Key'

<h3>💾 Saving and Loading</h3>

1. Users can navigate away from the app without losing session data
2. Users can close the app and return to it and restore temporary data
3. Users are wanred with a 'Unsaved Data' modal when attempting to exit the application
4. Users can save partial game sessions to the local memory
5. Users can load sessions from the local memory
6. Users can save player profiles peristently for tracking across multiple sessions and multiple games

<h3>⚡Court Interaction</h3>

1. User selects an area of the court and is met with a color circle gradient to visually confirm touch
2. User will receive pop-up box asking if the shot was 'Made', 'Miss', or 'Dunk'
    - For 'Made':
        - If shot was located within the 2pt area, the user selects 'And-1', 'From Rebound', or 'Layup'
        - If shot was located within the 3pt area, the user selects SHOT TYPE? 'Catch and Shoot' or 'Off the Dribble' and then is met with SHOT PRESSURE? 'Contested', 'Wide Open', 'End of Shot Clock'
    - For 'Missed':
        - User will be met with 'Airball', 'Rebound', and 'Turnover' as selectable options
3. After 'Made' sequence, the court is painted with a green dot
4. After 'Missed' sequence, the court is painted with a red dot
5. After 'Dunk' sequence, the court is painted with a gold dot

<h3> 🎯Additional Planned Features</h3>

- Color-coding or icons to represent different players on the heatmap, rather than uniform coloring that can be interpreted in the raw file
- Undo button that removes previous entries - dots on the map will not have selection boxes because adding new shots in similar places will be messy
- On selecting 'Game Finished', a pop-up summary of stats will appear presenting user friendly information for each player, selectable through a drop-down menu
- The pop-up summary will feature a 'compare' to assess the stats of two same-team players, where relevant
- Multi-Team Support: Users can load in default player profiles for an opposing team and track opponents shots
- Multi-Team Pop-Up: Users can compare home team summary stats with away team summary stats
- Multi-Team Pop-Up: Users can compare home team player with opposing team player
- On-Screen Score: Tracking home and opposing team scores as shots are tracked
- Switch between half-court view and full-court view at load
- Light mode v dark mode with different court designs for courtside use
- Load files from third-party cloud storage, like OneDrive.
- Add load screen for aesthetics and to address factors like player profiles and light or dark mode before entering

<h2>Installation</h2>

<pre>
git clone https://github.com/aarondsimpson/DunkVision.git
cd DunkVision
pip install -r requirements.txt
python project.py
</pre>

<h2> Project Layout</h2>

| Root        | Level 2       | Level 3         | File                 |Description                                                                          |
| :---------- |:--------------|:----------------|:---------------------|:------------------------------------------------------------------------------------|
|project.py   |               |                 |                      |Entry point to the Dunk Vision application, containing the main loop                 |
|             |assets         |                 |                      |Contains the assets required for the user interface                                  |
|             |               |screen_images    |                      |Contains load screen images and top-down court views                                 |
|             |               |mask_images      |                      |Contains mask images to support binary mask creation                                 |
|             |               |icons            |                      |Contains icons for creating local .exe                                               |
|             |               |fonts            |                      |Contains fonts used across the user-interface                                        |         
|             |session_data   |                 |                      |Contains persistent and temporary user data                                          | 
|             |               |player_profiles  |                      |Contains persistent player profiles across sessions                                  | 
|             |               |                 |default_profiles.json |Contains the default player profile data                                             |     
|             |               |                 |custom_profiles.json  |Contains the user-defined player profile data                                        |
|             |               |session_profiles |                      |Contains saved sessions and game data for loading                                    |
|             |               |tmp              |                      |Contains autosaves and file recovery data                                            |
|             |src            |                 |                      |Contains all application logic                                                       |
|             |               |                 |__ init __.py         |Ensures the 'src' folder is identified as a package                                  |                  
|             |               |                 |config.py             |Contains centralized application settings and pathing constants                      |
|             |               |user_interface   |                      |Contains all user interface modules                                                  | 
|             |               |                 |__ init __.py         |Ensures that the 'user interface' folder is identified as a package                  |
|             |               |                 |dunk_vision_app.py    |Controls and organizes all other UI files and is the entry point into UI             |
|             |               |                 |court_frames.py       |Controls the court view frame, including drawing zones and handling clicks           |
|             |               |                 |court_canvas.py       |Controls the rendering for court visuals and overlays                                |
|             |               |                 |modals.py             |Contains pop-up windows for user prompts and confirmations                           |
|             |               |                 |player_dialogs.py     |Contains UI dialogs for populating modals for prompts and confirmations              |
|             |               |                 |court_interactivity.py|Controls the court click plumbing and converts canvas cords to native image coords   |
|             |               |application_logic|                      |                                                                                     |
|             |               |                 |__ init __.py         |Ensures that the 'application_logic' folder is identified as a package               |
|             |               |                 |zoning.py             |Defines zones and handles click-hit detection                                        |
|             |               |                 |zone_configuration.py |Parameterizes zones and constants                                                    |
|             |               |devtools         |                      |Contains tools for probing click-hits, confirming zone boundaries, and recalibration |
|             |               |                 |__ init __.py         |Ensures that the 'devtools' folder is identified as a package                        |
|             |               |                 |probe_tool.py         |Developer tool to visualize click coordinates for zone detection and definition      |
|             |               |                 |calibration_tool.py   |Developer tool to recalibrate court bounding boxes                                   |
|             |               |                 |overlay_drawing.py    |Developer tool to draw overlays to confirm click boundaries and court zones          |
|             |               |                 |mask_builder.py       |Creates a binary mask image to map to assign user clicks to court boundaries         |
|             |               |data_analysis    |                      |Contains data analysis tools to handle collected data points that feed to modals     |
|             |               |                 |tbd.py                |Placeholder for undefined data analysis tools                                        |

<h2>Usage</h2>

1. Launch the application (python project.py)
2. Select "New Session" or "Load Session" from the load screen
3. (Optional) If "New Session", remove default player profiles from "My Team/Their Team" using the "remove" button in the left side bar
4. (Optional) If "New Session", add custom player profiles from "My Team/Their Team" using the "add" button in the left side bar
5. Select the game quarter using the quarter buttons in the top bar
6. Select the team to be tracked from the drop-down menu in the left side bar
7. Select the player to be tracked from the drop-down menu
8. Click on the court to record a shot
9. Complete the modal sequence to capture shot data
10. (Optional) If required, save the session to be loaded at a later time.
11. Click the "End Game" button to complete the shot tracking session.
12. Review the post-game data summary in the modal.
13. Click "Save Game" on the modal to save the game file for later review.
14. Click "Save Image" on the modal to save the heatmap shot image and/or the data summary image - or screenshot as required.
15. Click "Export" on the modal to export the game data as a JSON or CSV file. 


<h2>Use Cases</h2>

1. Coaches
- Identify team trends by analyzing shot location trends to target team-wide strengths and weaknesses to support training
- Identify player trends by analyzing player shot maps so that bespoke drills and performance goals can be designed
- Assess opposing teams by preparing solid defensive strategies on an opponent-by-opponent basis by understanding shot behavior
- Counter individual threats by understanding the patterns of key opposing players for better matchup planning

2. Parents
- College-recruitment support: parents support their players by capturing data during games to provide visual evidence of shot accuracy
- Compensate youth league gaps: support under-resourced and over-stretched youth leagues with game-changing capabilities

3. Players
- Train smarter: Support after-hours training and solo sessions by identifying and improving weak game areas
- Bragging rights: do you think you're better than your teammate, or your friends? Prove it with a shotmap and intuitive stats

<h2> ⭐Star This Repo? ⭐⁠</h2>

If you find **Dunk Vision** useful, please consider giving it a star on GitHub! It's a small gesture that helps others discover the project and motivates future updates. 
