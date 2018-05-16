# oif
Extract images and metadata from .oif files.

Write data contained in a `.oif` file to directories. Directories are
structured such that the basename of the `.oif` file (e.g. 
`/path/to/my/<basename>.oif`) is used as the parent directory. Each parent
directory then contains subdirectories for every channel contained in the
`.oif file`. Every channel subdirectory contains `.png` images for each
z-stack contained for that channel. Within each parent directory, a file
`metadata.json`, is also created to house annotated data for the embryo.

File structure example using `/path/to/my/<basename>.oif` with 3 Channels:
- out_dir
  - metadata.json
  - basename
  - Channel1
    - z0.png
    - z1.png
    - ...
  - Channel2
    - z0.png
    - z1.png
    - ...
  - Channel3
    - z0.png
    - z1.png
    - ...
    
The main script, `parse_oif.py` takes a single `.json` file as input with the
following format:

    {
    "oif_file": <location to oif file>,
    "stains": {"1": <stain used in first channel>,
               "2": <stain used in second channel>,
               "3": <stain used in third channel>,
               "4": <stain used in fourth channel>},
    "person": <name of person who collected the data>,
    "hpf": <hours past fertilization>,
    "treatment": <treatment applied to embryo>,
    "out_dir": <desired location to write output directories>,
    "prefix": <optinal string to write in front of output files>
    }
    
To run the script, issue the following command:
 
`python parse_oif.py <input.json>`
