

import os
import geopandas as gpd
import pandas as pd
import json
import shapely
from bokeh.io import output_file, show
from bokeh.models import BasicTicker, PrintfTickFormatter, TapTool, CustomJS, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool, Select, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
from bokeh.layouts import column, row
from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
from pyproj import Transformer

# Function to transform lat/lon to Web Mercator
def transform_to_web_mercator(gdf):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
    return gdf

# Load your shapefile using Geopandas
shapefile_path = r'"C:\Users\AbhilasaBarman\OneDrive - Azim Premji Foundation\Documents\SSP245&585_shp\SSP585_ClimateData_India.shp"'
gdf = gpd.read_file(shapefile_path)

# Ensure all relevant columns are numeric
numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
                   'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
                   'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
                   'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
                   'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
                   'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

for col in numeric_columns:
    gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# Transform coordinates to Web Mercator
gdf = transform_to_web_mercator(gdf)

# Convert the GeoDataFrame to GeoJSON format
gdf_json = json.loads(gdf.to_json())

# Create a GeoJSONDataSource from the GeoJSON data
geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# Define the output file
output_file("district_population_map.html", title="District Population Map")

# Create the figure
p = figure(
    title="District Population Map",
    x_axis_type="mercator",
    y_axis_type="mercator",
    tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
    width=900,
    height=800
)

# Add tile provider (map background)
p.add_tile("CartoDB Positron")

# Set initial map bounds to prevent resizing on selection
p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# Define color mappers for each parameter
parameter_palettes = {
    'Population': Turbo256,
    'HWDI_per_r': Viridis256,
    'HWDI_per_t': Inferno256,
    'Annual_RF_': Cividis256,
    'JJAS_RF_Ch': Plasma256,
    'OND_RF_Cha': Turbo256,
    'TMAX_Annua': Viridis256,
    'TMAX_MAM_C': Inferno256,
    'TMIN_Annua': Cividis256,
    'TMIN_DJF_C': Plasma256,
    'JJAS_CDD_P': Turbo256,
    'OND_CDD_Pe': Viridis256,
    'MAM_CSU_pe': Inferno256,
    'MAM_CSU__1': Cividis256,
    'WSDI_wrt_9': Plasma256,
    'Warm_spell': Turbo256,
    'JJAS_R10MM': Viridis256,
    'OND_R10MM_': Inferno256,
    'JJAS_R20MM': Cividis256,
    'OND_R20MM_': Plasma256,
    'RX1Day_JJA': Turbo256,
    'RX1Day_OND': Viridis256,
    'RX5day_JJA': Inferno256,
    'F5day_even': Cividis256,
    'RX5day_OND': Plasma256,
    'F5day_ev_1': Turbo256,
    'SDII_JJAS': Viridis256,
    'SDII_OND': Inferno256,
    'Rainy_Days': Cividis256,
    'Rainy_Da_1': Plasma256,
    'Summer_Day': Turbo256,
    'Annual_Wet': Viridis256,
    'MAM_Wet_Bu': Inferno256
}

# Define initial color mapper for population
initial_param = 'Population'
color_mapper = LinearColorMapper(palette=parameter_palettes[initial_param], low=gdf[initial_param].min(), high=gdf[initial_param].max())

# Add patches (polygons) to the figure
patches = p.patches(
    'xs', 'ys',
    source=geo_source,
    fill_color={'field': initial_param, 'transform': color_mapper},
    line_color="black",
    line_width=0.5,
    fill_alpha=0.7,
    name="patches"
)

# Add hover tool
hover = HoverTool()
hover.tooltips = [("State", "@State"), ("District", "@District"), (initial_param, f"@{initial_param}")]
p.add_tools(hover)

# Create a color bar for the population
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=10),
    formatter=PrintfTickFormatter(format="%.2f"),
    label_standoff=12,
    border_line_color=None,
    location=(0, 0)
)

p.add_layout(color_bar, 'left')

# Create a legend for the patches
legend = Legend(items=[LegendItem(label=initial_param, renderers=[patches])], location=(0, 0))
p.add_layout(legend, 'right')

# Create a Select widget for states
states = [''] + list(gdf['State'].unique())
state_select = Select(title="Select State:", value='', options=states)

# Create a Select widget for parameters
parameters = numeric_columns
parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# Function to create boxplot data for the selected state and parameter
def create_boxplot_data(state, parameter):
    if state:
        state_data = gdf[gdf['State'] == state]
        q1 = state_data[parameter].quantile(0.25)
        q2 = state_data[parameter].quantile(0.50)
        q3 = state_data[parameter].quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        lower = q1 - 1.5 * iqr
        return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])
    else:
        return dict(q1=[], q2=[], q3=[], upper=[], lower=[])

# Create initial boxplot data
initial_boxplot_data = create_boxplot_data('', parameters[0])
boxplot_source = ColumnDataSource(data=initial_boxplot_data)


# Create the initial boxplot
p_box = figure(title="Boxplot", width=600, height=400)
p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
p_box.xgrid.grid_line_color = None
p_box.y_range.start = 0
p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# Initial bar plot
initial_barplot_data = {'district': [], 'value': [], 'color': []}
barplot_source = ColumnDataSource(data=initial_barplot_data)

# Create the initial bar plot
p_bar = figure(title="Select a district and parameter", x_range=[], width=900, height=400)
p_bar.vbar(x='district', top='value', source=barplot_source, width=0.7, color='color')
p_bar.xgrid.grid_line_color = None
p_bar.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, barplot_source=barplot_source, p_box=p_box, p_bar=p_bar, state_select=state_select, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, hover=hover, parameter_palettes=parameter_palettes, legend=legend), code="""
    var data = source.data;
    var boxplot_data = boxplot_source.data;
    var state = state_select.value;
    var parameter = parameter_select.value;
    
    // Filter data for the selected state
    var indices = [];
    var parameter_data = [];
    for (var i = 0; i < data['State'].length; i++) {
        if (data['State'][i] == state) {
            indices.push(i);
            parameter_data.push(data[parameter][i]);
        }
    }
    
    // Update boxplot data if a state is selected
    if (state) {
        console.log("state",state)             
        console.log("parameter_Data",parameter_data)            
        var q1 = quantile(parameter_data, 0.25);
        var q2 = quantile(parameter_data, 0.50);
        var q3 = quantile(parameter_data, 0.75);
        var iqr = q3 - q1;
        var upper = q3 + 1.5 * iqr;
        var lower = q1 - 1.5 * iqr;

        boxplot_data['q1'] = [q1];
        boxplot_data['q2'] = [q2];
        boxplot_data['q3'] = [q3];
        boxplot_data['upper'] = [upper];
        boxplot_data['lower'] = [lower];
    } else {
        boxplot_data['q1'] = [];
        boxplot_data['q2'] = [];
        boxplot_data['q3'] = [];
        boxplot_data['upper'] = [];
        boxplot_data['lower'] = [];
    }
    boxplot_source.change.emit();
    
    // Update the color mapper and patches
    var new_palette = parameter_palettes[parameter];
    color_mapper.palette = new_palette;
    color_mapper.low = Math.min.apply(null, parameter_data);
    color_mapper.high = Math.max.apply(null, parameter_data);
    
    patches.glyph.fill_color = { field: parameter, transform: color_mapper };
    hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
    patches.change.emit();                
    source.change.emit();
    
    // Highlight the selected state
    var selected_indices = [];
    for (var i = 0; i < data['State'].length; i++) {
        if (data['State'][i] == state) {
            selected_indices.push(i);
        }
    }
    source.selected.indices = selected_indices;
    source.change.emit();
    
    // Update boxplot title
    p_box.title.text = parameter + " Boxplot for " + (state ? state : "Selected State");
    p_box.change.emit();
    
    // Update legend label
    legend.items[0].label = parameter;
    legend.items[0].renderers = [patches];
    legend.change.emit();
    
    // Helper function to calculate quantiles
    function quantile(arr, q) {
        const sorted = arr.slice().sort((a, b) => a - b);
        const pos = (sorted.length - 1) * q;
        const base = Math.floor(pos);
        const rest = pos - base;
        if ((sorted[base + 1] !== undefined)) {
            return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
        } else {
            return sorted[base];
        }
    }
""")

# Attach the callback to both Select widgets
state_select.js_on_change('value', callback)
parameter_select.js_on_change('value', callback)

# Attach the callback to the TapTool
taptool_callback = CustomJS(args=dict(source=geo_source, barplot_source=barplot_source, parameter_select=parameter_select, p_bar=p_bar, state_select=state_select, patches=patches), code="""
    var data = source.data;
    var barplot_data = barplot_source.data;
    var selected_index = source.selected.indices[0];
    var parameter = parameter_select.value;
    
    var selected_state = data['State'][selected_index];
    var selected_district = data['District'][selected_index];
    var district_data = [];
    var value_data = [];
    var color_data = [];
    var current_state = state_select.value;
    
    // Update bar plot based on selected district
    if (parameter) {
        for (var i = 0; i < data['State'].length; i++) {
            if (data['State'][i] == selected_state) {
                district_data.push(data['District'][i]);
                value_data.push(data[parameter][i]);
                color_data.push(data['District'][i] === selected_district ? "red" : "yellow");
            }
        }
        
        p_bar.title.text = parameter + " for " + selected_state;
        barplot_data['district'] = district_data;
        barplot_data['value'] = value_data;
        barplot_data['color'] = color_data;
        p_bar.x_range.factors = district_data;
        barplot_source.change.emit();
    } else {
        p_bar.title.text = "Select a district and parameter";
        barplot_data['district'] = [];
        barplot_data['value'] = [];
        barplot_data['color'] = [];
        p_bar.x_range.factors = [];
        barplot_source.change.emit();
    }
    
    // Highlight the selected district
    for (var i = 0; i < data['State'].length; i++) {
        data['color'][i] = i === selected_index ? "red" : "gray";
    }
    source.change.emit();
    patches.glyph.line_color = { field: 'color' };
""")
p.select(TapTool).callback = taptool_callback

# Layout the widgets and plots
layout = column(row(state_select, parameter_select), row(p, p_bar),p_box)

# Show the results
show(layout)



# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     'OND_RF_Cha': Turbo256,
#     'TMAX_Annua': Viridis256,
#     'TMAX_MAM_C': Inferno256,
#     'TMIN_Annua': Cividis256,
#     'TMIN_DJF_C': Plasma256,
#     'JJAS_CDD_P': Turbo256,
#     'OND_CDD_Pe': Viridis256,
#     'MAM_CSU_pe': Inferno256,
#     'MAM_CSU__1': Cividis256,
#     'WSDI_wrt_9': Plasma256,
#     'Warm_spell': Turbo256,
#     'JJAS_R10MM': Viridis256,
#     'OND_R10MM_': Inferno256,
#     'JJAS_R20MM': Cividis256,
#     'OND_R20MM_': Plasma256,
#     'RX1Day_JJA': Turbo256,
#     'RX1Day_OND': Viridis256,
#     'RX5day_JJA': Inferno256,
#     'F5day_even': Cividis256,
#     'RX5day_OND': Plasma256,
#     'F5day_ev_1': Turbo256,
#     'SDII_JJAS': Viridis256,
#     'SDII_OND': Inferno256,
#     'Rainy_Days': Cividis256,
#     'Rainy_Da_1': Plasma256,
#     'Summer_Day': Turbo256,
#     'Annual_Wet': Viridis256,
#     'MAM_Wet_Bu': Inferno256
# }

# # Define initial color mapper for population
# initial_param = 'Population'
# color_mapper = LinearColorMapper(palette=parameter_palettes[initial_param], low=gdf[initial_param].min(), high=gdf[initial_param].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': initial_param, 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), (initial_param, f"@{initial_param}")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'right')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper',0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = state_select.value;
#     var parameter = parameter_select.value;
    
#     // Filter data for the selected state
#     var indices = [];
#     var parameter_data = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     // Update boxplot data
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];
#     boxplot_source.change.emit();
    
#     // Update the color mapper and patches
#     var new_palette = parameter_palettes[parameter];
#     color_mapper.palette = new_palette;
#     color_mapper.low = Math.min.apply(null, parameter_data);
#     color_mapper.high = Math.max.apply(null, parameter_data);
    
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
#     hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
#     source.change.emit();
    
#     // Highlight the selected state
#     var selected_indices = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             selected_indices.push(i);
#         }
#     }
#     source.selected.indices = selected_indices;
#     source.change.emit();
    
#     // Update boxplot title
#     p_box.title.text = parameter + " Boxplot for " + state;
#     p_box.change.emit();
    
#     // Helper function to calculate quantiles
#     function quantile(arr, q) {
#         const sorted = arr.slice().sort((a, b) => a - b);
#         const pos = (sorted.length - 1) * q;
#         const base = Math.floor(pos);
#         const rest = pos - base;
#         if ((sorted[base + 1] !== undefined)) {
#             return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
#         } else {
#             return sorted[base];
#         }
#     }
# """)

# # Attach the callback to both Select widgets
# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', callback)

# # Layout the widgets and plots
# layout = row(column(state_select, parameter_select), p, p_box)

# # Show the results
# show(layout)



# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     'OND_RF_Cha': Turbo256,
#     'TMAX_Annua': Viridis256,
#     'TMAX_MAM_C': Inferno256,
#     'TMIN_Annua': Cividis256,
#     'TMIN_DJF_C': Plasma256,
#     'JJAS_CDD_P': Turbo256,
#     'OND_CDD_Pe': Viridis256,
#     'MAM_CSU_pe': Inferno256,
#     'MAM_CSU__1': Cividis256,
#     'WSDI_wrt_9': Plasma256,
#     'Warm_spell': Turbo256,
#     'JJAS_R10MM': Viridis256,
#     'OND_R10MM_': Inferno256,
#     'JJAS_R20MM': Cividis256,
#     'OND_R20MM_': Plasma256,
#     'RX1Day_JJA': Turbo256,
#     'RX1Day_OND': Viridis256,
#     'RX5day_JJA': Inferno256,
#     'F5day_even': Cividis256,
#     'RX5day_OND': Plasma256,
#     'F5day_ev_1': Turbo256,
#     'SDII_JJAS': Viridis256,
#     'SDII_OND': Inferno256,
#     'Rainy_Days': Cividis256,
#     'Rainy_Da_1': Plasma256,
#     'Summer_Day': Turbo256,
#     'Annual_Wet': Viridis256,
#     'MAM_Wet_Bu': Inferno256
# }

# # Define initial color mapper for population
# initial_param = 'Population'
# color_mapper = LinearColorMapper(palette=parameter_palettes[initial_param], low=gdf[initial_param].min(), high=gdf[initial_param].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': initial_param, 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), (initial_param, f"@{initial_param}")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'right')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper',0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = state_select.value;
#     var parameter = parameter_select.value;
    
#     // Filter data for the selected state
#     var indices = [];
#     var parameter_data = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     // Update boxplot data
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];
#     boxplot_source.change.emit();
    
#     // Update the color mapper and patches
#     var new_palette = parameter_palettes[parameter];
#     color_mapper.palette = new_palette;
#     color_mapper.low = Math.min.apply(null, parameter_data);
#     color_mapper.high = Math.max.apply(null, parameter_data);
    
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
#     hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
#     source.change.emit();
    
#     // Highlight the selected state
#     var selected_indices = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             selected_indices.push(i);
#         }
#     }
#     source.selected.indices = selected_indices;
#     source.change.emit();
    
#     // Update boxplot title
#     p_box.title.text = parameter + " Boxplot for " + state;
#     p_box.change.emit();
    
#     // Helper function to calculate quantiles
#     function quantile(arr, q) {
#         const sorted = arr.slice().sort((a, b) => a - b);
#         const pos = (sorted.length - 1) * q;
#         const base = Math.floor(pos);
#         const rest = pos - base;
#         if ((sorted[base + 1] !== undefined)) {
#             return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
#         } else {
#             return sorted[base];
#         }
#     }
# """)

# # Attach the callback to both Select widgets
# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', callback)

# # Layout the widgets and plots
# layout = row(column(state_select, parameter_select), p, p_box)

# # Show the results
# show(layout)



# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# # parameter_palettes = {
# #     'Population': Turbo256,
# #     'HWDI_per_r': Viridis256,
# #     'HWDI_per_t': Inferno256,
# #     'Annual_RF_': Cividis256,
# #     'JJAS_RF_Ch': Plasma256,
# #     # Add more mappings as needed
# # }
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     'OND_RF_Cha': Turbo256,
#     'TMAX_Annua': Viridis256,
#     'TMAX_MAM_C': Inferno256,
#     'TMIN_Annua': Cividis256,
#     'TMIN_DJF_C': Plasma256,
#     'JJAS_CDD_P': Turbo256,
#     'OND_CDD_Pe': Viridis256,
#     'MAM_CSU_pe': Inferno256,
#     'MAM_CSU__1': Cividis256,
#     'WSDI_wrt_9': Plasma256,
#     'Warm_spell': Turbo256,
#     'JJAS_R10MM': Viridis256,
#     'OND_R10MM_': Inferno256,
#     'JJAS_R20MM': Cividis256,
#     'OND_R20MM_': Plasma256,
#     'RX1Day_JJA': Turbo256,
#     'RX1Day_OND': Viridis256,
#     'RX5day_JJA': Inferno256,
#     'F5day_even': Cividis256,
#     'RX5day_OND': Plasma256,
#     'F5day_ev_1': Turbo256,
#     'SDII_JJAS': Viridis256,
#     'SDII_OND': Inferno256,
#     'Rainy_Days': Cividis256,
#     'Rainy_Da_1': Plasma256,
#     'Summer_Day': Turbo256,
#     'Annual_Wet': Viridis256,
#     'MAM_Wet_Bu': Inferno256
# }


# # Define initial color mapper for population
# color_mapper = LinearColorMapper(palette=parameter_palettes['Population'], low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),  # Adjusted format to display decimals
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper',0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = state_select.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];
    
#     boxplot_source.change.emit();
    
#     // Update the color mapper and patches
#     var new_palette = parameter_palettes[parameter];
#     color_mapper.palette = new_palette;
#     color_mapper.low = Math.min.apply(null, parameter_data);
#     color_mapper.high = Math.max.apply(null, parameter_data);
#     color_bar.color_mapper = color_mapper;

#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
#     hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
#     source.change.emit();
    
#     // Highlight the selected state
#     var selected_indices = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             selected_indices.push(i);
#         }
#     }
#     source.selected.indices = selected_indices;
#     source.change.emit();
    
#     // Update boxplot title
#     p_box.title.text = parameter + " Boxplot for " + state;
#     p_box.change.emit();
    
#     function quantile(arr, q) {
#         const sorted = arr.slice().sort((a, b) => a - b);
#         const pos = (sorted.length - 1) * q;
#         const base = Math.floor(pos);
#         const rest = pos - base;
#         if ((sorted[base + 1] !== undefined)) {
#             return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
#         } else {
#             return sorted[base];
#         }
#     }
# """)


# # Attach the callback to both Select widgets
# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', callback)

# # Layout the widgets and plots
# layout = row(column(state_select, parameter_select), p, p_box)

# # Show the results
# show(layout)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     # Add more mappings as needed
# }

# # Define initial color mapper for population
# color_mapper = LinearColorMapper(palette=parameter_palettes['Population'], low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),  # Adjusted format to display decimals
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - q3
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper',0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];
    
#     boxplot_source.change.emit();
    
#     // Update the color mapper and patches
#     var new_palette = parameter_palettes[parameter];
#     color_mapper.palette = new_palette;
#     color_mapper.low = Math.min.apply(null, parameter_data);
#     color_mapper.high = Math.max.apply(null, parameter_data);
#     color_bar.color_mapper = color_mapper;

#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
#     hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
#     source.change.emit();
    
#     // Highlight the selected state
#     var selected_indices = [];
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             selected_indices.push(i);
#         }
#     }
#     source.selected.indices = selected_indices;
#     source.change.emit();
    
#     // Update boxplot title
#     p_box.title.text = `${parameter} Boxplot for ${state}`;
    
#     function quantile(arr, q) {
#         const sorted = arr.slice().sort((a, b) => a - b);
#         const pos = (sorted.length - 1) * q;
#         const base = Math.floor(pos);
#         const rest = pos - base;
#         if ((sorted[base + 1] !== undefined)) {
#             return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
#         } else {
#             return sorted[base];
#         }
#     }
# """)

# # Attach the callback to both Select widgets
# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', callback)

# # Layout the widgets and plots
# layout = row(column(state_select, parameter_select), p, p_box)

# # Show the results
# show(layout)


# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     # Add more mappings as needed
# }

# # Define initial color mapper for population
# color_mapper = LinearColorMapper(palette=parameter_palettes['Population'], low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),  # Adjusted format to display decimals
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper',0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];
    
#     boxplot_source.change.emit();
    
#     // Update the color mapper and patches
#     var new_palette = parameter_palettes[parameter];
#     color_mapper.palette = new_palette;
#     color_mapper.low = Math.min.apply(null, parameter_data);
#     color_mapper.high = Math.max.apply(null, parameter_data);
#     color_bar.color_mapper = color_mapper;

#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
#     hover.tooltips = [["State", "@State"], ["District", "@District"], [parameter, "@" + parameter]];
#     source.change.emit();
    
#     // Update boxplot title
#     p_box.title.text = `${parameter} Boxplot for ${state}`;
    
#     function quantile(arr, q) {
#         const sorted = arr.slice().sort((a, b) => a - b);
#         const pos = (sorted.length - 1) * q;
#         const base = Math.floor(pos);
#         const rest = pos - base;
#         if ((sorted[base + 1] !== undefined)) {
#             return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
#         } else {
#             return sorted[base];
#         }
#     }
# """)

# # Attach the callback to both Select widgets
# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', callback)

# # Layout the widgets and plots
# layout = row(column(state_select, parameter_select), p, p_box)

# # Show the results
# show(layout)


# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256, Viridis256, Inferno256, Cividis256, Plasma256
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mappers for each parameter
# parameter_palettes = {
#     'Population': Turbo256,
#     'HWDI_per_r': Viridis256,
#     'HWDI_per_t': Inferno256,
#     'Annual_RF_': Cividis256,
#     'JJAS_RF_Ch': Plasma256,
#     # Add more mappings as needed
# }

# # Define initial color mapper for population
# color_mapper = LinearColorMapper(palette=parameter_palettes['Population'], low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),  # Adjusted format to display decimals
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
    
#     // Update color mapper for the selected parameter
#     color_mapper.low = Math.min(...parameter_data);
#     color_mapper.high = Math.max(...parameter_data);
#     color_mapper.palette = parameter_palettes[parameter];
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
    
#     // Update hover tool
#     hover.tooltips = [("State", "@State"), ("District", "@District"), (parameter, "@" + parameter)];
#     color_bar.color_mapper = color_mapper;
#     color_bar.formatter = PrintfTickFormatter(format="%d");
#     color_bar.title = parameter;

#     source.change.emit();
#     color_bar.change.emit();
#     patches.change.emit();
# """)

# # JavaScript callback for the parameter Select widget to update the boxplot and map
# parameter_callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover, parameter_palettes=parameter_palettes), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var parameter = cb_obj.value;
#     var state = state_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
    
#     // Update color mapper for the selected parameter
#     color_mapper.low = Math.min(...parameter_data);
#     color_mapper.high = Math.max(...parameter_data);
#     color_mapper.palette = parameter_palettes[parameter];
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
    
#     // Update hover tool
#     hover.tooltips = [("State", "@State"), ("District", "@District"), (parameter, "@" + parameter)];
#     color_bar.color_mapper = color_mapper;
#     color_bar.formatter = PrintfTickFormatter(format="%d");
#     color_bar.title = parameter;

#     source.change.emit();
#     color_bar.change.emit();
#     patches.change.emit();
# """)

# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', parameter_callback)

# # Layout
# layout = row(column(state_select, parameter_select), p, column(p_box), sizing_mode="stretch_both")
# show(layout)





# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256 as palette
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define initial color mapper for population
# color_mapper = LinearColorMapper(palette=palette, low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population")]
# p.add_tools(hover)

# # # Create a color bar for the population
# # color_bar = ColorBar(
# #     color_mapper=color_mapper,
# #     ticker=BasicTicker(desired_num_ticks=10),
# #     formatter=PrintfTickFormatter(format="%d"),
# #     label_standoff=12,
# #     border_line_color=None,
# #     location=(0, 0)
# # )
# # Create a color bar for the population with decimal values
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%.2f"),  # Adjusted format to display decimals
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )


# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
    
#     // Update color mapper for the selected parameter
#     color_mapper.low = Math.min(...parameter_data);
#     color_mapper.high = Math.max(...parameter_data);
#     color_mapper.palette = palette;
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
    
#     // Update hover tool
#     hover.tooltips = [("State", "@State"), ("District", "@District"), (parameter, "@" + parameter)];
#     color_bar.color_mapper = color_mapper;
#     color_bar.formatter = PrintfTickFormatter(format="%d");
#     color_bar.title = parameter;

#     source.change.emit();
# """)

# # JavaScript callback for the parameter Select widget to update the boxplot and map
# parameter_callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select, color_mapper=color_mapper, patches=patches, color_bar=color_bar, hover=hover), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var parameter = cb_obj.value;
#     var state = state_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
    
#     // Update color mapper for the selected parameter
#     color_mapper.low = Math.min(...parameter_data);
#     color_mapper.high = Math.max(...parameter_data);
#     color_mapper.palette = palette;
#     patches.glyph.fill_color = { field: parameter, transform: color_mapper };
    
#     // Update hover tool
#     hover.tooltips = [("State", "@State"), ("District", "@District"), (parameter, "@" + parameter)];
#     color_bar.color_mapper = color_mapper;
#     color_bar.formatter = PrintfTickFormatter(format="%d");
#     color_bar.title = parameter;

#     source.change.emit();
# """)

# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', parameter_callback)


# # Layout
# layout = row(column(state_select, parameter_select), p, column(p_box), sizing_mode="stretch_both")
# show(layout)
























# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256 as palette
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the Geo
# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mapper for population
# color_mapper = LinearColorMapper(palette=palette, low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population"), ("JJAS_CDD_P", "@JJAS_CDD_P")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%d"),
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - q3;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
# """)

# # JavaScript callback for the parameter Select widget to update the boxplot
# parameter_callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var parameter = cb_obj.value;
#     var state = state_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - q3;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
# """)

# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', parameter_callback)

# # Initialize empty data for scatter plot
# scatter_source = ColumnDataSource(data=dict(Annual_RF_=[], TMAX_Annua=[], State=[], District=[], color=[]))

# # Create the scatter plot
# p_scatter = figure(title="Annual_RF_ vs TMAX_Annua", width=450, height=400)
# scatter = p_scatter.scatter('Annual_RF_', 'TMAX_Annua', source=scatter_source, size=10, color='color', alpha=0.6)

# # Add hover tool to the scatter plot
# scatter_hover = HoverTool()
# scatter_hover.tooltips = [("Annual Rainfall", "@Annual_RF_"), ("Annual Max Temp", "@TMAX_Annua"), ("State", "@State"), ("District", "@District")]
# p_scatter.add_tools(scatter_hover)

# # JavaScript callback for the scatter plot color mapping based on state selection
# scatter_callback = CustomJS(args=dict(source=scatter_source, state_select=state_select, gdf_data=gdf.to_json()), code="""
#     var state = state_select.value;
#     var data = JSON.parse(gdf_data);
#     var scatter_data = {Annual_RF_: [], TMAX_Annua: [], State: [], District: [], color: []};
    
#     data.features.forEach(function(feature) {
#         if (feature.properties.State == state) {
#             scatter_data.Annual_RF_.push(feature.properties.Annual_RF_);
#             scatter_data.TMAX_Annua.push(feature.properties.TMAX_Annua);
#             scatter_data.State.push(feature.properties.State);
#             scatter_data.District.push(feature.properties.District);
#             scatter_data.color.push('red');
#         }
#     });
    
#     source.data = scatter_data;
#     source.change.emit();
# """)

# state_select.js_on_change('value', scatter_callback)

# # Layout
# layout = row(column(state_select, parameter_select), p, column(p_box, p_scatter), sizing_mode="stretch_both")
# show(layout)




# import os
# import geopandas as gpd
# import pandas as pd
# import json
# import shapely
# from bokeh.io import output_file, show
# from bokeh.models import BasicTicker, PrintfTickFormatter
# from bokeh.plotting import figure
# from bokeh.models import GeoJSONDataSource, HoverTool, Select, CustomJS, ColumnDataSource, Range1d, ColorBar, LinearColorMapper
# from bokeh.layouts import column, row
# from bokeh.palettes import Turbo256 as palette
# from pyproj import Transformer

# # Function to transform lat/lon to Web Mercator
# def transform_to_web_mercator(gdf):
#     transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
#     gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.ops.transform(transformer.transform, geom))
#     return gdf

# # Load your shapefile using Geopandas
# shapefile_path = r'C:\Users\AbhilasaBarman\Downloads\SSP245&585_shp\SSP245_ClimateData_India.shp'
# gdf = gpd.read_file(shapefile_path)

# # Ensure all relevant columns are numeric
# numeric_columns = ['Population', 'HWDI_per_r', 'HWDI_per_t', 'Annual_RF_', 'JJAS_RF_Ch', 'OND_RF_Cha', 
#                    'TMAX_Annua', 'TMAX_MAM_C', 'TMIN_Annua', 'TMIN_DJF_C', 'JJAS_CDD_P', 'OND_CDD_Pe', 
#                    'MAM_CSU_pe', 'MAM_CSU__1', 'WSDI_wrt_9', 'Warm_spell', 'JJAS_R10MM', 'OND_R10MM_', 
#                    'JJAS_R20MM', 'OND_R20MM_', 'RX1Day_JJA', 'RX1Day_OND', 'RX5day_JJA', 'F5day_even', 
#                    'RX5day_OND', 'F5day_ev_1', 'SDII_JJAS', 'SDII_OND', 'Rainy_Days', 'Rainy_Da_1', 
#                    'Summer_Day', 'Annual_Wet', 'MAM_Wet_Bu']

# for col in numeric_columns:
#     gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

# # Transform coordinates to Web Mercator
# gdf = transform_to_web_mercator(gdf)

# # Convert the GeoDataFrame to GeoJSON format
# gdf_json = json.loads(gdf.to_json())

# # Create a GeoJSONDataSource from the GeoJSON data
# geo_source = GeoJSONDataSource(geojson=json.dumps(gdf_json))

# # Define the output file
# output_file("district_population_map.html", title="District Population Map")

# # Create the figure
# p = figure(
#     title="District Population Map",
#     x_axis_type="mercator",
#     y_axis_type="mercator",
#     tools="pan,wheel_zoom,zoom_in,zoom_out,reset,tap",
#     width=900,
#     height=800
# )

# # Add tile provider (map background)
# p.add_tile("CartoDB Positron")

# # Set initial map bounds to prevent resizing on selection
# p.x_range = Range1d(start=gdf.total_bounds[0], end=gdf.total_bounds[2])
# p.y_range = Range1d(start=gdf.total_bounds[1], end=gdf.total_bounds[3])

# # Define color mapper for population
# color_mapper = LinearColorMapper(palette=palette, low=gdf['Population'].min(), high=gdf['Population'].max())

# # Add patches (polygons) to the figure
# patches = p.patches(
#     'xs', 'ys',
#     source=geo_source,
#     fill_color={'field': 'Population', 'transform': color_mapper},
#     line_color="black",
#     line_width=0.5,
#     fill_alpha=0.7,
#     name="patches"
# )

# # Add hover tool
# hover = HoverTool()
# hover.tooltips = [("State", "@State"), ("District", "@District"), ("Population", "@Population"), ("JJAS_CDD_P", "@JJAS_CDD_P")]
# p.add_tools(hover)

# # Create a color bar for the population
# color_bar = ColorBar(
#     color_mapper=color_mapper,
#     ticker=BasicTicker(desired_num_ticks=10),
#     formatter=PrintfTickFormatter(format="%d"),
#     label_standoff=12,
#     border_line_color=None,
#     location=(0, 0)
# )

# p.add_layout(color_bar, 'left')

# # Create a Select widget for states
# states = list(gdf['State'].unique())
# state_select = Select(title="Select State:", value=states[0], options=states)

# # Create a Select widget for parameters
# parameters = numeric_columns[1:]  # Excluding 'Population' for parameter selection
# parameter_select = Select(title="Select Parameter:", value=parameters[0], options=parameters)

# # Function to create boxplot data for the selected state and parameter
# def create_boxplot_data(state, parameter):
#     state_data = gdf[gdf['State'] == state]
#     q1 = state_data[parameter].quantile(0.25)
#     q2 = state_data[parameter].quantile(0.50)
#     q3 = state_data[parameter].quantile(0.75)
#     iqr = q3 - q1
#     upper = q3 + 1.5 * iqr
#     lower = q1 - 1.5 * iqr
#     return dict(q1=[q1], q2=[q2], q3=[q3], upper=[upper], lower=[lower])

# # Create initial boxplot data
# initial_boxplot_data = create_boxplot_data(states[0], parameters[0])
# boxplot_source = ColumnDataSource(data=initial_boxplot_data)

# # Create the initial boxplot
# p_box = figure(title=f"{parameters[0]} Boxplot for {states[0]}", width=450, height=400)
# p_box.segment(0, 'upper', 0, 'q3', source=boxplot_source, line_color="black")
# p_box.segment(0, 'lower', 0, 'q1', source=boxplot_source, line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q2', top='q3', source=boxplot_source, fill_color="#598090", line_color="black")
# p_box.vbar(x=0, width=0.7, bottom='q1', top='q2', source=boxplot_source, fill_color="#bb7b85", line_color="black")
# p_box.rect(0, 'upper', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.rect(0, 'lower', 0.2, 0.01, source=boxplot_source, line_color="black")
# p_box.xgrid.grid_line_color = None
# p_box.y_range.start = 0
# p_box.xaxis.major_label_orientation = 3.14 / 2  # Rotate x-axis labels vertically

# # JavaScript callback for the Select widgets for states and parameters to highlight state and update boxplot
# callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, parameter_select=parameter_select), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var state = cb_obj.value;
#     var parameter = parameter_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - 1.5 * iqr;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
# """)

# # JavaScript callback for the parameter Select widget to update the boxplot
# parameter_callback = CustomJS(args=dict(source=geo_source, boxplot_source=boxplot_source, p_box=p_box, state_select=state_select), code="""
#     var data = source.data;
#     var boxplot_data = boxplot_source.data;
#     var parameter = cb_obj.value;
#     var state = state_select.value;
#     var indices = [];
#     var parameter_data = [];
    
#     for (var i = 0; i < data['State'].length; i++) {
#         if (data['State'][i] == state) {
#             indices.push(i);
#             parameter_data.push(data[parameter][i]);
#         }
#     }
    
#     var q1 = quantile(parameter_data, 0.25);
#     var q2 = quantile(parameter_data, 0.50);
#     var q3 = quantile(parameter_data, 0.75);
#     var iqr = q3 - q1;
#     var upper = q3 + 1.5 * iqr;
#     var lower = q1 - q3;

#     boxplot_data['q1'] = [q1];
#     boxplot_data['q2'] = [q2];
#     boxplot_data['q3'] = [q3];
#     boxplot_data['upper'] = [upper];
#     boxplot_data['lower'] = [lower];

#     source.selected.indices = indices;
#     boxplot_source.change.emit();
#     source.change.emit();

#     p_box.title.text = parameter + " Boxplot for " + state;

#     function quantile(arr, q) {
#         arr.sort(function(a, b) { return a - b; });
#         var pos = (arr.length - 1) * q;
#         var base = Math.floor(pos);
#         var rest = pos - base;
#         if ((arr[base + 1] !== undefined)) {
#             return arr[base] + rest * (arr[base + 1] - arr[base]);
#         } else {
#             return arr[base];
#         }
#     }
# """)

# state_select.js_on_change('value', callback)
# parameter_select.js_on_change('value', parameter_callback)

# # Initialize empty data for scatter plot
# scatter_source = ColumnDataSource(data=dict(Annual_RF_=[], TMAX_Annua=[], State=[],District=[], color=[]))

# # Create the scatter plot
# p_scatter = figure(title="Annual_RF_ vs TMAX_Annua", width=450, height=400)
# scatter = p_scatter.scatter('Annual_RF_', 'TMAX_Annua', source=scatter_source, size=10, color='color', alpha=0.6)

# # Add hover tool to the scatter plot
# scatter_hover = HoverTool()
# scatter_hover.tooltips = [("Annual Rainfall", "@Annual_RF_"), ("Annual Max Temp", "@TMAX_Annua"), ("State", "@State"),("District", "@District")]
# p_scatter.add_tools(scatter_hover)

# # JavaScript callback for the scatter plot color mapping based on state selection
# scatter_callback = CustomJS(args=dict(source=scatter_source, state_select=state_select, gdf_data=gdf.to_json()), code="""
#     var state = state_select.value;
#     var data = JSON.parse(gdf_data);
#     var scatter_data = {Annual_RF_: [], TMAX_Annua: [], State: [], color: []};
    
#     data.features.forEach(function(feature) {
#         if (feature.properties.State == state) {
#             scatter_data.Annual_RF_.push(feature.properties.Annual_RF_);
#             scatter_data.TMAX_Annua.push(feature.properties.TMAX_Annua);
#             scatter_data.State.push(feature.properties.State);
#             scatter_data.color.push('red');
#         }
#     });
    
#     source.data = scatter_data;
#     source.change.emit();
# """)

# state_select.js_on_change('value', scatter_callback)

# # Layout
# layout = row(column(state_select, parameter_select), p, column(p_box, p_scatter), sizing_mode="stretch_both")
# show(layout)
