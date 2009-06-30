#!/usr/bin/env ruby

# Load a LW export into an SQLite DB
require 'rubygems'
require 'sequel'
require 'sequel/extensions/migration'
require 'fastercsv'

if ARGV.size < 2
  puts "Usage: load_export.rb export_dir file.db"
  exit 2
end

# Connect
db_path = File.expand_path(ARGV[1])
DB = Sequel.connect("sqlite://#{db_path}")

# Ensure migrated
migration_dir = File.expand_path(File.join(__FILE__, '/../migrations'))
Sequel::Migrator.apply(DB, migration_dir)

def load_file(filename)
  table = filename.to_sym

  DB[table].delete
  FasterCSV.foreach(File.join(ARGV[0], filename + '.csv'), :row_sep => "\r\n") do |row|
    DB[table] << row
  end
end

# Load data
%w(users articles comments article_votes comment_votes).each do |filename|
  puts "Loading #{filename}"
  load_file filename
end

DB.disconnect
