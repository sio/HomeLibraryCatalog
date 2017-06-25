% rebase("main")

<style>
.rTable {
    display: table;
    border: 1px solid #cccccc;
    }
.rTableRow {
    display: table-row;
    }
.rTableHeading {
    display: table-header-group;
    }
.rTableHead {
    font-weight: bold;
    }
.rTableBody {
    display: table-row-group;
    }
.rTableFoot {
    display: table-footer-group;
    }
.rTableCell, .rTableHead {
    display: table-cell;
    padding: 0.25em;
    border: 1px solid #cccccc;
    }
</style>

<div class="rTable">
% if cursor:
    <div class="rTableHeading">
    % for field in [x[0] for x in cursor.description]:
        <div class="rTableHead">{{field}}</div>
    % end
    </div>
    % for row in cursor.fetchall():
        <div class="rTableRow">
        % for value in row:
            <div class="rTableCell">\\
            <%
            if type(value) is bytes:
                value = "<BLOB>"
            end
            %>
            {{value}}</div>
        % end
        </div>
    % end
% end
</div>
