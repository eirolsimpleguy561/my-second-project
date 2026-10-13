import json
import os
import argparse

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = self.parse_value(value)
        self.save_config()
    
    def delete(self, key):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                print(f"Key '{key}' not found.")
                return
            config = config[k]
        if keys[-1] in config:
            del config[keys[-1]]
            self.save_config()
        else:
            print(f"Key '{key}' not found.")
    
    def parse_value(self, value):
        # Try to parse as JSON value
        try:
            return json.loads(value)
        except:
            pass
        
        # Handle common types
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.lower() == 'null':
            return None
        try:
            return int(value)
        except:
            pass
        try:
            return float(value)
        except:
            pass
        return value
    
    def list_keys(self, prefix=""):
        def recurse(d, current_path):
            keys = []
            for k, v in d.items():
                path = f"{current_path}.{k}" if current_path else k
                if isinstance(v, dict):
                    keys.extend(recurse(v, path))
                else:
                    keys.append((path, v))
            return keys
        
        for path, value in recurse(self.config, ""):
            if prefix in path:
                print(f"{path}: {json.dumps(value)}")
    
    def export_to_yaml(self, output_file):
        import yaml
        with open(output_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        print(f"Exported to {output_file}")
    
    def export_to_ini(self, output_file):
        import configparser
        config_parser = configparser.ConfigParser()
        
        def flatten_dict(d, section="DEFAULT"):
            for k, v in d.items():
                if isinstance(v, dict):
                    flatten_dict(v, k)
                else:
                    if section not in config_parser:
                        config_parser[section] = {}
                    config_parser[section][k] = str(v)
        
        flatten_dict(self.config)
        with open(output_file, 'w') as f:
            config_parser.write(f)
        print(f"Exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="JSON Configuration Manager")
    parser.add_argument("--file", default="config.json", help="Configuration file path")
    parser.add_argument("action", choices=["get", "set", "delete", "list", "export"], help="Action to perform")
    parser.add_argument("--key", help="Configuration key (dot notation)")
    parser.add_argument("--value", help="Value to set")
    parser.add_argument("--format", choices=["yaml", "ini"], default="yaml", help="Export format")
    parser.add_argument("--output", help="Output file for export")
    
    args = parser.parse_args()
    
    config_mgr = ConfigManager(args.file)
    
    if args.action == "get":
        if not args.key:
            print("Please specify --key")
            return
        value = config_mgr.get(args.key)
        print(json.dumps(value, indent=2) if value is not None else "Key not found")
    
    elif args.action == "set":
        if not args.key or args.value is None:
            print("Please specify --key and --value")
            return
        config_mgr.set(args.key, args.value)
        print(f"Set {args.key} = {args.value}")
    
    elif args.action == "delete":
        if not args.key:
            print("Please specify --key")
            return
        config_mgr.delete(args.key)
    
    elif args.action == "list":
        config_mgr.list_keys(args.key or "")
    
    elif args.action == "export":
        output = args.output or f"export.{args.format}"
        if args.format == "yaml":
            config_mgr.export_to_yaml(output)
        else:
            config_mgr.export_to_ini(output)

if __name__ == "__main__":
    # Interactive mode if no arguments
    if len(os.sys.argv) == 1:
        manager = ConfigManager()
        while True:
            print("\n=== Config Manager ===")
            print("1. List config")
            print("2. Get value")
            print("3. Set value")
            print("4. Delete key")
            print("5. Exit")
            
            choice = input("Choose: ").strip()
            
            if choice == '1':
                manager.list_keys()
            elif choice == '2':
                key = input("Key: ").strip()
                print(manager.get(key))
            elif choice == '3':
                key = input("Key: ").strip()
                value = input("Value: ").strip()
                manager.set(key, value)
            elif choice == '4':
                key = input("Key: ").strip()
                manager.delete(key)
            elif choice == '5':
                break
    else:
        main()
