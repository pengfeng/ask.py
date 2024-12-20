# Re-importing necessary libraries and recreating the flowchart due to a reset.
import matplotlib.patches as patches
import matplotlib.pyplot as plt

# Create a figure
fig, ax = plt.subplots(figsize=(10, 14))


# Helper function to create a box
def create_box(text, x, y, width=2.5, height=0.8, color="lightblue"):
    ax.add_patch(
        patches.Rectangle(
            (x, y), width, height, edgecolor="black", facecolor=color, lw=1.5
        )
    )
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=10)


# Helper function to create an arrow
def create_arrow(x_start, y_start, x_end, y_end):
    ax.annotate(
        "",
        xy=(x_end, y_end),
        xytext=(x_start, y_start),
        arrowprops=dict(facecolor="black", shrink=0.05, width=1.5, headwidth=8),
    )


# Draw the flowchart components
create_box("Start", 4, 12)
create_box("Query Input", 4, 10.5)
create_box("Mode Selection", 4, 9)
create_box("Search Mode", 1.5, 7.5)
create_box("Local Mode", 6.5, 7.5)
create_box("Search Google", 1.5, 6)
create_box("Crawl and Scrape Results", 1.5, 4.5)
create_box("Use Local Files", 6.5, 6)
create_box("Extract Text Content", 6.5, 4.5)
create_box("Chunk Text Content", 4, 3)
create_box("Save to VectorDB", 4, 1.5)
create_box("Perform Hybrid Search", 4, 0)
create_box("[Optional] Re-rank Results", 4, -1.5)
create_box("Use Top Chunks as Context", 4, -3)
create_box("Generate Answer with References", 4, -4.5)
create_box("Output Answer", 4, -6)

# Draw the arrows
create_arrow(5.25, 12, 5.25, 11.3)
create_arrow(5.25, 10.5, 5.25, 9.8)
create_arrow(5.25, 9, 3.5, 8.3)  # to Search Mode
create_arrow(5.25, 9, 6.5, 8.3)  # to Local Mode
create_arrow(2.75, 7.5, 2.75, 6.8)  # to Search Google
create_arrow(7.75, 7.5, 7.75, 6.8)  # to Use Local Files
create_arrow(2.75, 6, 2.75, 5.3)  # to Crawl and Scrape Results
create_arrow(7.75, 6, 7.75, 5.3)  # to Extract Text Content
create_arrow(2.75, 4.5, 4, 3.8)  # to Chunk Text Content
create_arrow(7.75, 4.5, 6, 3.8)  # to Chunk Text Content
create_arrow(5.25, 3, 5.25, 2.3)  # to Save to VectorDB
create_arrow(5.25, 1.5, 5.25, 0.8)  # to Perform Hybrid Search
create_arrow(5.25, 0, 5.25, -0.8)  # to Optional Re-rank Results
create_arrow(5.25, -1.5, 5.25, -2.3)  # to Use Top Chunks as Context
create_arrow(5.25, -3, 5.25, -3.8)  # to Generate Answer with References
create_arrow(5.25, -4.5, 5.25, -5.3)  # to Output Answer

# Final touches
ax.axis("off")
plt.title("Flowchart of Query Processing System", fontsize=14)
plt.show()
