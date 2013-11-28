<?php
/**
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 * http://www.gnu.org/copyleft/gpl.html
 *
 * @author Rob Church <robchur@gmail.com>
 */

/**
 * This is a MediaWiki maintenance script. Copy it to the maintenance
 * directory of your MediaWiki installation, and run with php from the
 * command-line.
 */

require_once __DIR__ . '/Maintenance.php';

class DeleteTestAccounts extends Maintenance {
    public function __construct() {
        parent::__construct();
        $this->addOption( 'delete', 'Actually delete the accounts' );
    }

    public function execute() {

        $this->output( "Remove test accounts\n\n" );

        $users_to_remove = array(
            'noemail',
            'bobtest',
            'iamslow'
        );
        $del = array();
        $dbr = wfGetDB( DB_SLAVE );
        $res = $dbr->select( 'user', array( 'user_id', 'user_name'), '', __METHOD__ );

        foreach ( $res as $row ) {
            $instance = User::newFromId( $row->user_id );
            if ( in_array($row->user_name, $users_to_remove) )
            {
                $del[] = $row->user_id;
                $this->output( $row->user_name . "\n" );
            }
        }
        $count = count( $del );
        $this->output( "...found {$count}.\n" );

        # If required, go back and delete each marked account
        if ( $count > 0 && $this->hasOption( 'delete' ) ) {
            $this->output( "\nDeleting unused accounts..." );
            $dbw = wfGetDB( DB_MASTER );
            $dbw->delete( 'user', array( 'user_id' => $del ), __METHOD__ );
            $dbw->delete( 'user_groups', array( 'ug_user' => $del ), __METHOD__ );
            $dbw->delete( 'user_former_groups', array( 'ufg_user' => $del ), __METHOD__ );
            $dbw->delete( 'user_properties', array( 'up_user' => $del ), __METHOD__ );
            $dbw->delete( 'logging', array( 'log_user' => $del ), __METHOD__ );
            $dbw->delete( 'recentchanges', array( 'rc_user' => $del ), __METHOD__ );
            $this->output( "done.\n" );
            # Update the site_stats.ss_users field
            $users = $dbw->selectField( 'user', 'COUNT(*)', array(), __METHOD__ );
            $dbw->update( 'site_stats', array( 'ss_users' => $users ), array( 'ss_row_id' => 1 ), __METHOD__ );
        } elseif ( $count > 0 ) {
            $this->output( "\nRun the script again with --delete to remove them from the database.\n" );
        }
        $this->output( "\n" );
    }
}

$maintClass = "DeleteTestAccounts";
require_once RUN_MAINTENANCE_IF_MAIN;
