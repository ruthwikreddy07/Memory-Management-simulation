import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt # Import the plotting library

# --- Memory Management Logic (This part remains unchanged) ---
class MemoryManager:
    def __init__(self, total_memory):
        self.total_memory = total_memory
        self.memory = [{'start': 0, 'size': total_memory, 'status': 'free', 'process_id': None}]

    def _merge_free_blocks(self):
        self.memory.sort(key=lambda b: b['start'])
        i = 0
        while i < len(self.memory) - 1:
            current = self.memory[i]
            next_block = self.memory[i+1]
            if current['status'] == 'free' and next_block['status'] == 'free':
                current['size'] += next_block['size']
                self.memory.pop(i+1)
            else:
                i += 1
    
    def _split_block(self, block_index, process_id, size):
        block = self.memory[block_index]
        if block['size'] > size:
            new_free_block = {
                'start': block['start'] + size,
                'size': block['size'] - size,
                'status': 'free',
                'process_id': None
            }
            self.memory.insert(block_index + 1, new_free_block)
        
        block['size'] = size
        block['status'] = 'used'
        block['process_id'] = process_id
        return f"SUCCESS: Allocated Process {process_id} ({size}KB)."

    def first_fit(self, process_id, size):
        for i, block in enumerate(self.memory):
            if block['status'] == 'free' and block['size'] >= size:
                return self._split_block(i, process_id, size)
        return f"FAIL: Not enough memory for Process {process_id}."

    def best_fit(self, process_id, size):
        best_block_index = -1
        min_fragmentation = float('inf')
        for i, block in enumerate(self.memory):
            if block['status'] == 'free' and block['size'] >= size:
                fragmentation = block['size'] - size
                if fragmentation < min_fragmentation:
                    min_fragmentation = fragmentation
                    best_block_index = i
        
        if best_block_index != -1:
            return self._split_block(best_block_index, process_id, size)
        return f"FAIL: Not enough memory for Process {process_id}."

    def worst_fit(self, process_id, size):
        worst_block_index = -1
        max_fragmentation = -1
        for i, block in enumerate(self.memory):
            if block['status'] == 'free' and block['size'] >= size:
                fragmentation = block['size'] - size
                if fragmentation > max_fragmentation:
                    max_fragmentation = fragmentation
                    worst_block_index = i
        
        if worst_block_index != -1:
            return self._split_block(worst_block_index, process_id, size)
        return f"FAIL: Not enough memory for Process {process_id}."

    def deallocate(self, process_id):
        for block in self.memory:
            if block['status'] == 'used' and block['process_id'] == process_id:
                block['status'] = 'free'
                block['process_id'] = None
                self._merge_free_blocks()
                return f"SUCCESS: Deallocated Process {process_id}."
        return f"FAIL: Process {process_id} not found."

    def get_fragmentation(self):
        free_blocks = [b for b in self.memory if b['status'] == 'free']
        if len(free_blocks) <= 1:
            return 0
        total_free_memory = sum(b['size'] for b in free_blocks)
        largest_free_block = max(b['size'] for b in free_blocks)
        return total_free_memory - largest_free_block

# --- Streamlit User Interface ---

st.set_page_config(page_title="Memory Management Sim", layout="wide")

if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = MemoryManager(total_memory=1024)

# --- NEW VISUALIZATION FUNCTION (using Matplotlib) ---
def create_memory_plot(mm):
    """Generates a Matplotlib figure representing the memory state."""
    fig, ax = plt.subplots(figsize=(10, 1.5))
    
    current_pos = 0
    for block in mm.memory:
        size = block['size']
        status = block['status']
        process_id = block['process_id']
        
        color = '#4CAF50' if status == 'used' else '#f44336'
        
        # Draw the bar for the block
        ax.barh([0], [size], left=[current_pos], color=color, edgecolor='white', height=0.8)
        
        # Add text label inside the bar
        label = f"{process_id}\n({size}KB)" if status == 'used' else f"Free\n({size}KB)"
        ax.text(current_pos + size / 2, 0, label, ha='center', va='center', color='white', fontsize=8)
        
        current_pos += size

    # Formatting the plot to look clean
    ax.set_xlim(0, mm.total_memory)
    ax.set_yticks([]) # Hide y-axis
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_xlabel("Memory Address (KB)")
    
    return fig

# --- UI Layout (Mostly the same) ---
st.title("🧠 Memory Management Simulation")

with st.sidebar:
    st.header("Controls")
    with st.form("memory_form"):
        process_id = st.text_input("Process ID (e.g., P1)")
        process_size = st.number_input("Process Size (KB)", min_value=1, value=128)
        algorithm = st.selectbox("Allocation Algorithm", ('First-Fit', 'Best-Fit', 'Worst-Fit'))
        col1, col2 = st.columns(2)
        with col1:
            allocate_button = st.form_submit_button("Allocate", type="primary")
        with col2:
            deallocate_button = st.form_submit_button("Deallocate")

    if st.button("Reset Simulation"):
        st.session_state.memory_manager = MemoryManager(total_memory=1024)
        st.success("Simulation has been reset.")

mm = st.session_state.memory_manager

if allocate_button:
    if not process_id or process_size <= 0:
        st.error("Please provide a valid Process ID and Size.")
    else:
        algo_map = {'First-Fit': mm.first_fit, 'Best-Fit': mm.best_fit, 'Worst-Fit': mm.worst_fit}
        message = algo_map[algorithm](process_id, process_size)
        if "SUCCESS" in message:
            st.success(message)
        else:
            st.error(message)

if deallocate_button:
    if not process_id:
        st.error("Please provide a Process ID to deallocate.")
    else:
        message = mm.deallocate(process_id)
        if "SUCCESS" in message:
            st.info(message)
        else:
            st.warning(message)

st.header("Memory Visualization")
# --- DISPLAY THE NEW MATPLOTLIB PLOT ---
fig = create_memory_plot(mm)
st.pyplot(fig)


st.header("Current State & Metrics")
col1, col2 = st.columns(2)
with col1:
    fragmentation = mm.get_fragmentation()
    st.metric(label="External Fragmentation", value=f"{fragmentation} KB")
with col2:
    used_memory = sum(b['size'] for b in mm.memory if b['status'] == 'used')
    st.metric(label="Total Used Memory", value=f"{used_memory} / {mm.total_memory} KB")

st.subheader("Memory Blocks Table")
df = pd.DataFrame(mm.memory)
st.dataframe(df)