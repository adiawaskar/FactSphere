# Memory Requirements for FactSphere

FactSphere uses large language models to analyze misinformation in trending topics. These models require significant system resources, particularly memory.

## System Requirements

For optimal performance:
- **RAM**: At least 8GB, 16GB recommended
- **Free Disk Space**: At least 5GB for models and data
- **Virtual Memory/Paging File**: At least 8GB

## Common Memory Issues

### The paging file is too small for this operation to complete (OS Error 1455)

This error occurs when Windows doesn't have enough virtual memory to load the model.

#### How to Fix

##### 1. Increase Virtual Memory (Paging File Size)

1. Right-click on **This PC** or **My Computer** and select **Properties**
2. Click on **Advanced system settings**
3. In the System Properties window, click the **Advanced** tab
4. Click the **Settings** button under **Performance**
5. In the Performance Options window, click the **Advanced** tab
6. Click the **Change** button under **Virtual memory**
7. Uncheck **Automatically manage paging file size for all drives**
8. Select the drive where Windows is installed (usually C:)
9. Select **Custom size** and set:
   - **Initial size (MB)**: 8192 (8GB)
   - **Maximum size (MB)**: 16384 (16GB)
10. Click **Set**, then **OK** to apply changes
11. Restart your computer

##### 2. Use the Lightweight Agent

If you cannot increase virtual memory, FactSphere provides a lightweight alternative:

```
POST /api/agent/analyze/lightweight
```

The lightweight agent uses smaller models that require less memory but may provide less accurate results.

##### 3. Close Memory-Intensive Applications

Before running analysis, close other memory-intensive applications like:
- Web browsers with many tabs
- Video editing software
- Virtual machines
- Other AI or ML applications

## Monitoring Memory Usage

You can monitor your system's memory usage:

1. Press **Ctrl+Shift+Esc** to open Task Manager
2. Click on the **Performance** tab
3. Check "Memory" usage during analysis

If usage consistently reaches maximum available memory, consider upgrading your system RAM.
