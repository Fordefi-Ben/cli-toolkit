"""Summary command - quick overview of logs."""

import click
from ..extractor import load_logs
from ..parser import parse_file, extract_app_info, get_all_modules


@click.command()
@click.argument('source', type=click.Path(exists=True))
def summary(source: str):
    """Show a quick summary of the log files.
    
    SOURCE can be a zip file or directory containing flog*.txt files.
    """
    click.echo(click.style("\n📊 Log Summary", fg="cyan", bold=True))
    click.echo(click.style("─" * 40, fg="cyan"))
    
    try:
        logs = load_logs(source)
        
        if not logs.log_files:
            click.echo(click.style("❌ No log files found", fg="red"))
            return
        
        # Get app info from first file
        app_info = extract_app_info(logs.log_files[0])
        
        # Parse all entries
        all_entries = []
        for log_file in logs.log_files:
            all_entries.extend(parse_file(log_file))
        
        # Sort by timestamp
        all_entries.sort(key=lambda e: e.timestamp)
        
        # Calculate stats
        error_count = sum(1 for e in all_entries if e.level == 'error')
        modules = get_all_modules(all_entries)
        
        # Date range
        if all_entries:
            first_ts = all_entries[0].timestamp.strftime('%Y-%m-%d %H:%M')
            last_ts = all_entries[-1].timestamp.strftime('%Y-%m-%d %H:%M')
            date_range = f"{first_ts} → {last_ts}"
        else:
            date_range = "N/A"
        
        # File stats
        size_mb = logs.total_size / (1024 * 1024)
        
        # Display
        click.echo(f"{'Files:':<14} {len(logs.log_files)} logs ({size_mb:.1f} MB)")
        click.echo(f"{'Date Range:':<14} {date_range}")
        click.echo()
        
        # Device info
        click.echo(click.style("📱 Device", fg="yellow", bold=True))
        click.echo(f"{'  Model:':<14} {app_info.device_type or 'Unknown'} {app_info.device_model or ''}")
        click.echo(f"{'  OS:':<14} {app_info.os_name or 'Unknown'} {app_info.os_version or ''}")
        click.echo(f"{'  App Version:':<14} {app_info.version or 'Unknown'}")
        click.echo()
        
        # Entry stats
        click.echo(click.style("📈 Stats", fg="yellow", bold=True))
        click.echo(f"{'  Entries:':<14} {len(all_entries):,}")
        click.echo(f"{'  Errors (⛔):':<14} {error_count}")
        click.echo(f"{'  Modules:':<14} {len(modules)}")
        click.echo()
        
        # Top modules
        if modules:
            module_counts = {}
            for e in all_entries:
                if e.module:
                    module_counts[e.module] = module_counts.get(e.module, 0) + 1
            
            top_modules = sorted(module_counts.items(), key=lambda x: -x[1])[:5]
            click.echo(click.style("🏷️  Top Modules", fg="yellow", bold=True))
            for mod, count in top_modules:
                click.echo(f"  [{mod}]: {count}")
        
        # Cleanup
        logs.cleanup()
        
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
