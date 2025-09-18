<h1>🏀 Dunk Vision</h1>

Dunk Vision is a basketball shot tracker and spatial data capture tool built using Python (3.12.10) and tkinter. Designed for youth coaches, players, and parents, it lets users track, visualize, export, and analyze shot data to improve individual and team performance on-court and in-training. 

<h2>❓ Rationale </h2>

Youth organizations are propped up by limited funding, over-stretched coaches, burned-out parents, and the goodwill of local communities. Jerseys often escape the budget. Lunch is provided by turn-taking parents. Training is last-minute as coaches and teenagers balance their personal lives.  

Supporting my stepson through middle school basketball, high school basketball, summer camps, youth leagues, and local competitions, it became clear that he and his teammates were going to struggle to receive the support that they needed, paid to receive, and deserved, to move them forward in their sports careers. 

For this reason, I built a tool that turns wild pickup games into strategic opportunities, last-minute training sessions into focused workshops, and bus-rides home into structured pre-game and post-game briefs where hazy memory, hunches, and napkin scribbles are thrown out in favor of robust, real-time data analysis. I built a tool that helps busy coaches react to the patterns and trends they missed while juggling parent politics, a tool that helps parents understand their children's role on the court with accessible metrics, and a tool that helps players focus on developing within their lane. I wanted a tool that would turn a team winning 1 out of every 5 games into a team that stood a chance of winning every time they step onto the court. 


<h2>💻 Installation</h2>

<h3>Clone the Repository</h3>
<pre>
git clone https://github.com/aarondsimpson/DunkVision.git
cd DunkVision
</pre>
<h3> Install Dependencies</h3>
<pre>
pip install -r requirements.txt
</pre>
<h3> Run the App</h3>
<pre>
python project.py
</pre>


<h2>🌳 Project Layout</h2>

| Root           | Level 1       | Level 2         | Level 3                  |Description                                                                             |
| :--------------|:--------------|:----------------|:-------------------------|:---------------------------------------------------------------------------------------|
|gitignore.py    |               |                 |                          |Ruleset for Git, preventing tracking and committing for environmental stuff             |
|README.md       |               |                 |                          |README document describing structure and installation instructions                      |
|project.py      |               |                 |                          |Entry point to the Dunk Vision application, containing the main loop                    |
|requirements.txt|               |                 |                          |Contains the librarires required for installation                                       |
|test_project.py |               |                 |                          |Contains several tests for functions within project.py                                  |
|                |assets         |                 |                          |Contains the assets required for the user interface                                     |
|                |               |__ init __.py    |                          |Ensures the 'assets' folder is identified as a package                                  |
|                |               |screen_images    |                          |Contains load screen images and top-down court views                                    |
|                |               |mask_images      |                          |Contains mask images to support binary mask creation                                    |
|                |               |icons            |                          |Contains icons for creating local .exe                                                  |
|                |               |fonts            |                          |Contains fonts used across the user-interface                                           | 
|                |session_data   |                 |                          |Contains persistent and temporary user data                                             | 
|                |               |__ init __.py    |                          |Ensures the 'session_data' folder is identified as a package                            |
|                |               |custom_team.json |                          |Stores custom team schema for pre-saved and custom teams                                |
|                |               |game_io.py       |                          |Creates save game files from the court-state and outputs a 'dv-game.json' file          |
|                |               |team_store.py    |                          |Uses the custom team schema to create and safe-write new teams to persistent memory     |
|                |               |tmp              |                          |Stores temporary files for crash protection, user sessions, and exports pre-confirmation|
|                |               |                 |__ init __.py             |Ensures the 'tmp' folder is identified as a package as harmless boilerplate             |
|                |src            |                 |                          |Contains all application logic                                                          |
|                |               |__ init __.py    |                          |Ensures the 'src' folder is identified as a package                                |      
|                |               |config.py        |                          |Contains centralized application settings and pathing constants                         |
|                |               |application_logic|                          |Controls the court mask and court zone logic for data analysis and shot recognition     |
|                |               |                 |__ init __.py             |Ensures that the 'application_logic' folder is identified as a package                  |
|                |               |                 |court_mask_color_ledger.py|Defines zones by RGB signatures for later access                                        |
|                |               |                 |mask_manager.py           |Inspects the mask image and maps click coordinates to an RGB zone defined in the mask   |
|                |               |                 |zoning.py                 |Defines zones and handles click-hit detection                                           |
|                |               |                 |zoning_configuration.py   |Normalizes click coordinates and connects mask data to game logic                       |
|                |               |user_interface   |                          |Contains all user interface modules                                                     | 
|                |               |                 |__ init __.py             |Ensures that the 'user interface' folder is identified as a package                     |
|                |               |                 |court_canvas.py           |Controls the rendering for court visuals and overlays                                   |
|                |               |                 |court_frames.py           |Controls the court view frame, including drawing zones and handling clicks              |
|                |               |                 |dunk_vision_controller.py |Controls and organizes all other UI files and is the entry point into UI                |
|                |               |                 |modals.py                 |Contains pop-up windows for user prompts and confirmations                              |
|                |               |                 |player_dialogs.py         |Contains UI dialogs for populating modals for prompts and confirmations                 |


<h2>📋 Usage</h2>

1. Launch the application
2. Select "New" or "Load" from the start screen
    - If "New ", edit the default "My Team" and "Their Team" teams by renaming the teams and adding, removing, or renaming players.
    - If "Load", re-select the persistently saved teams to the "My Team" and "Their Team" slot to continue tracking shots. 
3. Select the game quarter to ensure shots are tracked in the correct quarter, then select the player to be tracked from the team roster.
4. Click on the court to record a shot, completing the modal sequence to gather shot data and update the scoreboard. 
5. Review the real-time data analysis card on the right of the screen as shots are recorded throughout the game. 
6. Select "Save Game" to create a "dv-game.json" file that can be loaded later for review or further tracking. 
7. Select "Export Image" to create a ".png" of the court showing the shot locations. 
8. Export game data for further analysis by selecting "Export CSV" or "Export JSON".

> ⚠️ Note: Once new teams are added, you must first have "My Team" selected, then select the new team from the dropdown to swap it with "My Team" to have that custom team appear as *your team*. Equally, when adding a team for "Their Team", you must select "Their Team" first, then the dropdown, then select the new team to swap it and record it as the opponent team.  



<h2>💡 Use Cases</h2>

- 👉 **Coaches**
    - Spot team-wide trends for shot locations, distances, and zones to build a picture of how the team uses court space
    - Review player shot maps to create custom drills and assign individualized performance goals
    - Monitor opposing team strengths and weaknesses and create solid defensive strategies on a team-by-team basis
    - Counter individual threats by using player data to create better matchup plans

- 👉 **Parents**
    - Support your children by capturing and recording their in-game data to provide visual and textual evidence of performance
    - Fill the gaps left by youth leagues by providing your children with the coaching advice they need from real performances

- 👉 **Players**
    - Use after-hours training and solo session time more intelligently by identifying and improving personalized weaknesses
    - Do you think you're better than your teammate, or your friends? Prove it with a shotmap and intuitive stats. If you really dunk more, then prove it. 

<h2> ⭐Star This Repo? ⭐⁠</h2>

If you find **Dunk Vision** useful, please consider giving it a star on GitHub! It's a small gesture that helps parents, players, and coaches discover the project and motivates future updates. 
